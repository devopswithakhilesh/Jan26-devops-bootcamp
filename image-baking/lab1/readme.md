


```bash
# Dev build

packer validate -var-file="dev-al2023.auto.pkrvars.hcl" .
packer build -var-file="dev-al2023.auto.pkrvars.hcl" .

```

```bash
# Prod build

packer validate -var-file="prod-al2023.auto.pkrvars.hcl" .

packer build -var-file="prod-al2023.auto.pkrvars.hcl" .

```