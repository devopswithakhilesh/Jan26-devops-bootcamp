# import os

# date= os.getenv("DATE")
# print(date)

# if date is None:
#     print("DATE is not set")
#     exit(1)

# print(f"DATE is set to {date}")

# import subprocess

# result = subprocess.run(["ls", "-l"], capture_output=True, text=True)
# print(result.stdout)


# create a file and write
# with open("test.txt", "w") as f:
#     f.write("Hello, World!")

# read the file
# with open("test.txt", "r") as f:
#     print(f.read())

# # delete the file
# import os
# os.remove("test.txt")


old_host = "rds-migration.cvik8accw2tk.ap-south-1.rds.amazonaws.com"
rds_instance_id = old_host.split('.')[0]
host_part = ''.join(['.'.join(old_host.split('.')[1:])])
print(f'rds instance id: {rds_instance_id}')
print(f'host part: {host_part}')

new_host = f"{rds_instance_id}-new.{host_part}"
print(f'new host: {new_host}')