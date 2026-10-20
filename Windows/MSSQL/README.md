# .NET app to a domain VM database

This PC is in the `contoso` domain. The SQL Server VM `sqldb` (`10.1.2.10`) is in the `contosocom` domain, so Windows authentication from this PC only works when Visual Studio is started as a `contosocom` account with `runas /netonly`.

The default account is `CONTOSOCOM\table_owner`. A personal `contosocom` account may be used for a short dev test. Remove that personal login from `sqldb` when the test is finished, and leave `table_owner` in place.

Do this once: hosts file, connection strings, and the SQL login. After that, only the start steps are needed each day.

## 1. Confirm the hosts file

`C:\Windows\System32\drivers\etc\hosts` must contain:

```
10.1.2.10 sqldb.contosocom.example
10.1.2.11 appvm.contosocom.example
```

`sqldb` is the SQL Server used below. `appvm` does not accept SQL connections from this PC (port 1433 is closed). Leave Audit and App pointed at `sqldb`.

## 2. Set the connection strings

In `MyApp.Api\appsettings.json`, Audit and App match the dev environment:

```
Data Source=sqldb.contosocom.example;Initial Catalog=AuditLogs; Integrated Security=True; TrustServerCertificate=True;
Data Source=sqldb.contosocom.example;Initial Catalog=AppDb; Integrated Security=True; TrustServerCertificate=True;
```

`MyApp.Web\appsettings.json` uses the same Audit string.

App in appsettings is the connection name. The database is `AppDb`.

The GIS strings stay on `sqldb` with a SQL login. They do not use the Windows account.

## 3. Grant the Windows login on sqldb

RDP to `10.1.2.10` and open SSMS as `sa`. The `contosocom` account needs `db_datareader` and `db_datawriter` on `AuditLogs` and `AppDb`. Replace `<sample>` with that account name. `CONTOSOCOM\table_owner` is the usual account.

Skip this section if that user already exists. To create it:

```sql
USE [master];
CREATE LOGIN [CONTOSOCOM\<sample>] FROM WINDOWS;

USE [AuditLogs];
CREATE USER [CONTOSOCOM\<sample>] FOR LOGIN [CONTOSOCOM\<sample>];
ALTER ROLE db_datareader ADD MEMBER [CONTOSOCOM\<sample>];
ALTER ROLE db_datawriter ADD MEMBER [CONTOSOCOM\<sample>];

USE [AppDb];
CREATE USER [CONTOSOCOM\<sample>] FOR LOGIN [CONTOSOCOM\<sample>];
ALTER ROLE db_datareader ADD MEMBER [CONTOSOCOM\<sample>];
ALTER ROLE db_datawriter ADD MEMBER [CONTOSOCOM\<sample>];
```

If you do not create a login for the `contoso` account you use to sign in to Visual Studio, `sqldb` cannot see that account (SQL error 15401).

After dev testing, remove `CONTOSOCOM\<sample>` from `AuditLogs`, `App`, and `AppDb`. Replace `<sample>` with the personal account used for the test. Keep `table_owner`.

```sql
USE [AuditLogs];
DROP USER [CONTOSOCOM\<sample>];

USE [App];
DROP USER [CONTOSOCOM\<sample>];

USE [AppDb];
DROP USER [CONTOSOCOM\<sample>];

USE [master];
DROP LOGIN [CONTOSOCOM\<sample>];
```

## 4. Start Visual Studio

Close any Visual Studio window that was opened with your normal PC sign-in.

On this PC, open Command Prompt and run:

```cmd
runas /netonly /user:CONTOSOCOM\table_owner "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\devenv.exe"
```

Enter the password for `table_owner` or the other account created in step 3. A normal Run as different user fails on the local PC and reports a bad username or password. `/netonly` uses that account only for network connections, which is what SQL Server sees.

Open the solution and start `MyApp.AppHost`.

A Run as different user session does not pop up a browser when you start debugging. Aspire still prints the address in the AppHost output. Find the line that starts with "Login to the dashboard", copy the whole URL including `?t=`, and paste it into the browser you already have open.

The token changes every start. Opening `https://localhost:17204/login` with no token shows a token prompt.

## When a start fails

Error 18452, login from an untrusted domain: the API is running as the `contoso` sign-in for this PC. Close Visual Studio and repeat step 4 with `CONTOSOCOM\table_owner`.

Error 40, with Windows error 1326 or error 2, and the server name is `appvm.contosocom.example`: Audit or App still points at `appvm`. Repeat step 2 and start again.

Error 15401 while creating the `contoso` sign-in: expected. Use a `CONTOSOCOM` account, as in step 3.
