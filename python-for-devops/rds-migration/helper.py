import boto3
import psycopg2
import time
from botocore.config import Config
from psycopg2 import OperationalError
import logging
from botocore.exceptions import ClientError
import subprocess



db_link = 'postgresql://postgres:Admin1234@rds-migration.cvik8accw2tk.ap-south-1.rds.amazonaws.com:5432/postgres'
rds = boto3.client('rds', region_name='ap-south-1')
ec2_client = boto3.client('ec2', region_name='ap-south-1')
# get rds details for a given rds instance
def get_source_rds_details(rds_instance_id):
    response = rds.describe_db_instances(DBInstanceIdentifier=rds_instance_id)
    return response['DBInstances'][0]

# parge the db_link to get the user, password, host, port, db_name
def parse_db_link(db_link):
    # postgresql://postgres:Admin1234@rds-migration.cvik8accw2tk.ap-south-1.rds.amazonaws.com:5432/postgres
    user = db_link.split('://')[1].split(':')[0]
    password = db_link.split('@')[0].split(':')[-1]
    host = db_link.split('@')[1].split(':')[0]
    db_name = db_link.split('@')[1].split("/")[-1]
    port = db_link.split(":")[-1].split("/")[0]

    # print(user, password, host, db_name, port)
    return user, password, host, db_name, port



def duplicate_rds(rds_instance_id, new_allocated_storage):
    source_rds_data = get_source_rds_details(rds_instance_id)
    
    user, password, host, db_name, port = parse_db_link(db_link)

    instance_params = {
        "DBName": db_name,
        "DBInstanceIdentifier": f"{source_rds_data['DBInstanceIdentifier']}-new",
        "AllocatedStorage": new_allocated_storage,
        "DBInstanceClass": source_rds_data["DBInstanceClass"],
        "Engine": source_rds_data["Engine"],
        "MasterUsername": user,
        "MasterUserPassword": password,
        "Port": int(port),
        "DBSecurityGroups": [
            items["DBSecurityGroupName"]
            for items in source_rds_data["DBSecurityGroups"]
        ],
        "VpcSecurityGroupIds": [
            items["VpcSecurityGroupId"]
            for items in source_rds_data["VpcSecurityGroups"]
        ],
        "AvailabilityZone": source_rds_data["AvailabilityZone"],
        "DBSubnetGroupName": source_rds_data["DBSubnetGroup"]["DBSubnetGroupName"],
        "PreferredMaintenanceWindow": source_rds_data["PreferredMaintenanceWindow"],
        "DBParameterGroupName": source_rds_data["DBParameterGroups"][0][
            "DBParameterGroupName"
        ],
        "BackupRetentionPeriod": source_rds_data["BackupRetentionPeriod"],
        "PreferredBackupWindow": source_rds_data["PreferredBackupWindow"],
        "MultiAZ": source_rds_data["MultiAZ"],
        "EngineVersion": source_rds_data["EngineVersion"],
        "AutoMinorVersionUpgrade": source_rds_data["AutoMinorVersionUpgrade"],
        "LicenseModel": source_rds_data["LicenseModel"],
        "OptionGroupName": source_rds_data["OptionGroupMemberships"][0][
            "OptionGroupName"
        ],
        "PubliclyAccessible": source_rds_data["PubliclyAccessible"],
        "Tags": source_rds_data["TagList"],
        "StorageType": source_rds_data["StorageType"],
        "StorageEncrypted": source_rds_data["StorageEncrypted"],
        "KmsKeyId": source_rds_data["KmsKeyId"],
        "CopyTagsToSnapshot": source_rds_data["CopyTagsToSnapshot"],
        "EnableIAMDatabaseAuthentication": source_rds_data[
            "IAMDatabaseAuthenticationEnabled"
        ],
        "EnablePerformanceInsights": source_rds_data["PerformanceInsightsEnabled"],
        "DeletionProtection": source_rds_data["DeletionProtection"],
        "EnableCustomerOwnedIp": source_rds_data["CustomerOwnedIpEnabled"],
        "BackupTarget": source_rds_data["BackupTarget"],
        "NetworkType": source_rds_data["NetworkType"],
        "CACertificateIdentifier": source_rds_data["CACertificateIdentifier"],
    }

    try:
        if source_rds_data["MaxAllocatedStorage"]:
            instance_params["MaxAllocatedStorage"] = source_rds_data[
                "MaxAllocatedStorage"
            ]
    except KeyError:
        pass

    response = rds.create_db_instance(**instance_params)
    return response

def check_rds_availability(host, port, dbname, user, password):
    while True:
        
        try:
            print(f"Checking RDS availability for {host}:{port}:{dbname}:{user}:{password}")
            # Attempt to establish a connection to the RDS database
            conn = psycopg2.connect(
                host=host, port=port, dbname=dbname, user=user, password=password
            )

            conn.close()
            time.sleep(30) # giving additional 30 seconds 
            return True

        except OperationalError as e:
            # If an OperationalError occurs (e.g., connection error), print the error
            print(f"Error connecting to the RDS database {host}: {e}")
            print("Retrying in 60 seconds...")
            time.sleep(60) 



def revoke_sgs(from_sg, to_sg, port):
    try:
        ec2_client.revoke_security_group_egress(
            GroupId=from_sg,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": port,
                    "ToPort": port,
                    "UserIdGroupPairs": [
                        {
                            "Description": "Lambda access",
                            "GroupId": to_sg,
                        }
                    ],
                }
            ],
        )
        logging.debug("ECS outbound rule for sg '%s' removed", from_sg)
    except ClientError as error:
        if error.response["Error"]["Code"] != "InvalidPermission.NotFound":
            logging.error("sg egress change failed: %s", error)
            raise error
    try:
        ec2_client.revoke_security_group_ingress(
            GroupId=to_sg,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": port,
                    "ToPort": port,
                    "UserIdGroupPairs": [
                        {
                            "Description": "Lambda access",
                            "GroupId": from_sg,
                        }
                    ],
                }
            ],
        )
        logging.debug("inbound rule for sg '%s' removed", to_sg)
    except ClientError as error:
        if error.response["Error"]["Code"] != "InvalidPermission.NotFound":
            logging.error("sg ingress change failed: %s", error)
            raise error

    logging.info("SG '%s' -/-> '%s' done", from_sg, to_sg)

def allow_sgs(from_sg, to_sg, port):
    # from_sg is the source security group attach to ecs 
    # to_sg is the destination security group attach to rds
    # port is the port to allow
    try:
        ec2_client.authorize_security_group_egress(
            GroupId=from_sg,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": port,
                    "ToPort": port,
                    "UserIdGroupPairs": [
                        {
                            "Description": "Lambda access",
                            "GroupId": to_sg,
                        }
                    ],
                }
            ],
        )
        logging.debug("Lambda outbound rule for sg '%s' done", from_sg)
    except ClientError as error:
        if error.response["Error"]["Code"] != "InvalidPermission.Duplicate":
            logging.error("sg egress change failed: %s", error)
            raise error
    try:
        ec2_client.authorize_security_group_ingress(
            GroupId=to_sg,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": port,
                    "ToPort": port,
                    "UserIdGroupPairs": [
                        {
                            "Description": "Lambda access",
                            "GroupId": from_sg,
                        }
                    ],
                }
            ],
        )
        logging.debug("inbound rule for sg '%s' done", to_sg)
    except ClientError as error:
        if error.response["Error"]["Code"] != "InvalidPermission.Duplicate":
            logging.error("sg ingress change failed: %s", error)
            raise error

    logging.info("ECS inbound rule SG '%s' -> '%s' done", from_sg, to_sg)


def rename_rds(old, new):
    try:
        rds.modify_db_instance(
            DBInstanceIdentifier=old, NewDBInstanceIdentifier=new, ApplyImmediately=True
        )
        logging.info(f"DB renamed - {new}")
    except Exception as e:
        logging.error(f"Issue with renaming {old} -> {new} : {e}")
        exit(1)


def timeout_handler(signum, frame):
    raise TimeoutError("Timed out after as RDS is not ready to take connection")

def swap_db(old, new):
    logging.info(f"Renaming db: {old} -> {old}-old ")
    rename_rds(old, f"{old}-old")
    time.sleep(300)  # Adding time delay to wait for db renaming
    logging.info(f"Renaming db: {new} - > {old}")
    rename_rds(new, old)

def stop_rds(dbinstance):
    try:
        logging.info(f"Stopping the RDS instance - {dbinstance}")
        rds.stop_db_instance(DBInstanceIdentifier=dbinstance)
    except Exception as e:
        logging.error(f"Issue with stopping - {dbinstance} -> {e}")
        exit(1)

def sync_dbs(old_db, new_db):
    # Create pgsync configuration with source and destination db details
    logging.info("Creating .pgsync.yml with source and destination db links")
    with open(".pgsync.yml", "w") as f:
        f.write(f"from: {old_db}\n")
        f.write(f"to: {new_db}\n")
        f.write("to_safe: true\n")
    # pgsync
    logging.info(f"Syncing DB's {old_db} -> {new_db}")
    try:
        process = subprocess.Popen(
            ["pgsync", "--schema-first", "--all-schemas"],
            stdout=subprocess.PIPE,
        )
        output = process.communicate()[0]
        if int(process.returncode) != 0:
            logging.error(f"Command failed. Return code : {process.returncode}")
        else:
            logging.info("Sync completed ")
        return output
    except Exception as e:
        logging.error(f"Issue with db sync -> {e}")
        exit(1)


def migrate_db(db_link):
    
    # parse the db_link to get the user, password, host, port, db_name
    user, password, host, db_name, port = parse_db_link(db_link)
    print(user, password, host, db_name, port)
    rds_instance_id = host.split('.')[0]
    host_part = ''.join(['.'.join(host.split('.')[1:])])
    print(f'source rds instance endpoint(host): {host}')
    print(f'source rds instance id: {rds_instance_id}')

    # source_rds_data = get_source_rds_details(rds_instance_id)
    # print(f'source rds data: {source_rds_data}')

    duplicate_rds(rds_instance_id, 20)
    
    new_rds_instance_id = f"{rds_instance_id}-new"
    new_host = f"{new_rds_instance_id}.{host_part}"
    print(f'new rds instance endpoint(host): {new_host}')
    print(f'new rds instance id: {new_rds_instance_id}')

    check_rds_availability(new_host, port, db_name, user, password)
    # allow the sgs
    # sync the db's
    print(f'syncing the db: {host} -> {new_host}')
    time.sleep(10)
    source_db_link = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    destination_db_link = f"postgresql://{user}:{password}@{new_host}:{port}/{db_name}"
    sync_dbs(source_db_link, destination_db_link)
    # revoke the sgs
    # swap the db's
    print(f'swapping the db: {rds_instance_id} -> {new_rds_instance_id}')
    swap_db(rds_instance_id, new_rds_instance_id)
    print(f'db swapped: {rds_instance_id} -> {new_rds_instance_id}')
    # stop the old rds instance
    print(f'stopping the old rds instance: {rds_instance_id}')
    stop_rds(rds_instance_id)
    print(f'old rds instance stopped: {rds_instance_id}')
    return True
    

if __name__ == "__main__":
    migrate_db(db_link)