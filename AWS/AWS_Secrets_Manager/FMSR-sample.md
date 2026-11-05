# FMSR Sample: Secrets Manager IAM Setup (QA)

## Prerequisite: Customer Managed KMS Key

The customer managed key must exist before Parts 1 and 2 are applied.

- Create the key in `ap-southeast-1` as a symmetric key with key usage Encrypt and decrypt.
- Keep the default key policy statement with Sid `Enable IAM User Permissions`. This lets Parts 1 and 2 grant use of the key.
- Share the key ARN with the application team for use when creating secrets.
- Replace `KMS_KEY_UUID` in Parts 1 and 2 with the key ID, which is the last segment of the key ARN.

## Part 1: Console User Access (IAM Console)

Attach this policy to the console team's IAM users or groups.

- `ConsoleTeamListSecrets` lists secrets.
- `ConsoleTeamManagement` creates, updates, and views secrets.
- `ConsoleTeamEncryptDecryptWithKMS` uses the key through Secrets Manager only.

Replace `XXXXXXXXXXXX` with the AWS account ID and `KMS_KEY_UUID` with the key ID.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ConsoleTeamListSecrets",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:ListSecrets"
            ],
            "Resource": "*"
        },
        {
            "Sid": "ConsoleTeamManagement",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:CreateSecret",
                "secretsmanager:UpdateSecret",
                "secretsmanager:DeleteSecret",
                "secretsmanager:TagResource",
                "secretsmanager:GetSecretValue",
                "secretsmanager:BatchGetSecretValue",
                "secretsmanager:PutSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:ap-southeast-1:XXXXXXXXXXXX:secret:*"
            ]
        },
        {
            "Sid": "ConsoleTeamEncryptDecryptWithKMS",
            "Effect": "Allow",
            "Action": [
                "kms:GenerateDataKey",
                "kms:Decrypt"
            ],
            "Resource": "arn:aws:kms:ap-southeast-1:XXXXXXXXXXXX:key/KMS_KEY_UUID",
            "Condition": {
                "StringEquals": {
                    "kms:ViaService": "secretsmanager.ap-southeast-1.amazonaws.com"
                }
            }
        }
    ]
}
```

## Part 2: Application Server Access (IAM Console)

Create an EC2 IAM role for UAT and PRD, for example `ec2-uat-project-secrets-role` and `ec2-prd-project-secrets-role`. Attach this policy to the application EC2 instances.

- `ApplicationListSecrets` lists secrets.
- `ApplicationReadSecret` reads secret values.
- `ApplicationDecryptWithKMS` decrypts secrets through Secrets Manager only.

Replace `XXXXXXXXXXXX` with the AWS account ID and `KMS_KEY_UUID` with the key ID. Secrets added later are covered without changing this policy.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ApplicationListSecrets",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:ListSecrets"
            ],
            "Resource": [
                "arn:aws:secretsmanager:ap-southeast-1:XXXXXXXXXXXX:secret:*"
            ]
        },
        {
            "Sid": "ApplicationReadSecret",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:BatchGetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:ap-southeast-1:XXXXXXXXXXXX:secret:*"
            ]
        },
        {
            "Sid": "ApplicationDecryptWithKMS",
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": "arn:aws:kms:ap-southeast-1:XXXXXXXXXXXX:key/KMS_KEY_UUID",
            "Condition": {
                "StringEquals": {
                    "kms:ViaService": "secretsmanager.ap-southeast-1.amazonaws.com"
                }
            }
        }
    ]
}
```
