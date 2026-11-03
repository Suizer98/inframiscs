# Outside EC2: mock the instance role without an access key

On an EC2 instance, `boto3` takes temporary credentials from the instance profile. Local working machine never receives that role. To run these scripts the same way, with no access key in the file, sign in through IAM Identity Center and let `boto3` use that permission set.

Leave the client as region only, and set `AWS_PROFILE` in the shell before `python aws_secret_manager_get.py`:

```python
client = boto3.client("secretsmanager", region_name="ap-southeast-1")
```

Or pass the profile name in code:

```python
session = boto3.Session(profile_name="dev")
client = session.client("secretsmanager", region_name="ap-southeast-1")
```

Either way `boto3` uses the SSO session.

## QA / PROD on EC2

The job uses the instance role. There is no `aws sso login` on those servers.

1. Open EC2, Instances, and select the QA or PROD batch-job VM.
2. Security tab, IAM role. Copy that role name.
3. Open the role in IAM, Roles.
4. Copy the role ARN (`arn:aws:iam::<account-id>:role/<role-name>`) and the 12-digit account id inside it.
5. On Permissions, confirm Secrets Manager: `ListSecrets`, `GetSecretValue`, `BatchGetSecretValue`. Create also needs create, put, tag, and delete.

On that box, omit `aws_access_key_id` and `aws_secret_access_key`. `boto3` uses the instance role. Keep that role on the instance. A customer-managed KMS key also needs `kms:GenerateDataKey`, `kms:Decrypt`, and `kms:DescribeKey` on that key.

## Local DEV: SSO

A PC uses IAM Identity Center, then a permission set that can read the same DEV secrets.

### SSO start URL and region

Open IAM Identity Center (sometimes still labelled AWS SSO). Settings, Identity source. Copy:

- AWS access portal URL, such as `https://d-xxxxxxxxxx.awsapps.com/start` or `https://your-company.awsapps.com/start`
- Region, here `ap-southeast-1`

That URL is the SSO start URL in `aws configure sso`.

The Identity Center user Profile page shows only the user. It has no start URL and no role. Copy those from Settings and from the AWS accounts tab.

### Account and permission set

Open the access portal, or in Identity Center open AWS accounts. Click the DEV account and copy:

- Account ID, 12 digits
- Account name
- Permission set name, for example `DeveloperAccess`

In the CLI, the permission set name is the SSO role name.

On the same user, the AWS accounts tab (next to Profile / Groups) lists each account id and permission set. An empty tab means the user exists and has no account assignment. Identity Center admin has to assign a permission set before SSO login has a role to assume.

## Configure the CLI

After `aws --version` works:

```text
aws configure sso
```

| CLI prompt | Paste from the dashboard |
| --- | --- |
| SSO session name | any local name, for example `contoso` |
| SSO start URL | Identity Center access portal URL |
| SSO region | Identity Center region |
| SSO registration scopes | `sso:account:access` |
| CLI default client Region | `ap-southeast-1` |
| CLI default output format | `json` |
| Profile name | any local nickname, for example `dev` |

The wizard lists accounts and permission sets. Pick the DEV account and the permission set that can read Secrets Manager. The profile name stays on this machine.

```text
aws configure list-profiles
```

Use one of those names as `--profile` and as `profile_name` in the session above.

```powershell
aws sso login --profile dev
aws sts get-caller-identity
aws secretsmanager list-secrets --region ap-southeast-1 --filters Key=tag-key,Values=Environment Key=tag-value,Values=DEV
```

`get-caller-identity` should show an ARN with `assumed-role` and the permission set name. After that, keep the keys out of the Python client.

## KMS key

We can use a customer-managed KMS key in `ap-southeast-1`. Secrets Manager encrypts the secret with that key on create, and decrypts with the same key when the secret is read. The key stays in KMS. A retrieve call does not send the key id. The key id is stored on the secret.

`aws_secret_manager_create.py` sends `kms_key_id` as `KmsKeyId` on every create. Set that constant to this alias before a run. If the name already exists, the script writes the value and then calls `update_secret` with the same key.

The alias below is a local name. Skip create when that alias already exists. Use the same profile as `aws sso login`.

1. Set the profile and region.

   ```powershell
   $env:AWS_PROFILE = "dev"
   $env:AWS_REGION = "ap-southeast-1"
   ```

2. Create the key. Skip this step when the alias already exists.

   ```powershell
   aws kms create-key --description "Secrets Manager KMS key"
   ```

3. Copy the `KeyId` from the output, then create the alias and turn on rotation.

   ```powershell
   aws kms create-alias --alias-name alias/<name> --target-key-id <KeyId>
   aws kms enable-key-rotation --key-id <KeyId>
   ```

4. Check the alias. `KeyState` should be `Enabled`. Press `q` to leave the pager.

   ```powershell
   aws kms describe-key --key-id alias/<name>
   ```

5. To rename the alias, delete it and create the new name on the same key.

   ```powershell
   aws kms delete-alias --alias-name alias/<name>
   aws kms create-alias --alias-name alias/<new-name> --target-key-id <KeyId>
   ```

## Create a secret with that key

`create-secret` takes `--kms-key-id`. The alias works. Tags match `aws_secret_manager_create.py`: `Environment=DEV` and `Application=SCHEDULEDJOBS`.

String secret:

```powershell
aws secretsmanager create-secret `
  --name "<secret-name>" `
  --secret-string "<secret-value>" `
  --kms-key-id alias/<name> `
  --tags Key=Environment,Value=DEV Key=Application,Value=SCHEDULEDJOBS `
  --region ap-southeast-1
```

Move an existing secret onto this key. Secrets Manager re-encrypts the current value:

```powershell
aws secretsmanager update-secret `
  --secret-id "<secret-name>" `
  --kms-key-id alias/<name> `
  --region ap-southeast-1
```

Confirm the key. `KmsKeyId` in the output is the key ARN:

```powershell
aws secretsmanager describe-secret --secret-id "<secret-name>" --region ap-southeast-1
```
