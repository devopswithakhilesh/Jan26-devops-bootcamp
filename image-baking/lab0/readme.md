# install packer
https://developer.hashicorp.com/packer/tutorials/docker-get-started/get-started-install-cli


```bash 
packer init .       # download the amazon plugin
packer fmt .        # format the file
packer validate .   # sanity-check before building
packer build .      # build the AMI
```