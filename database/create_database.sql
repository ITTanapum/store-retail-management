/*
Run this script while connected to the master database with a SQL Server administrator account.
Change the password below, then put the same value in backend/.env.
*/

USE [master];
GO

IF DB_ID(N'store_retail_db') IS NULL
BEGIN
    CREATE DATABASE [store_retail_db];
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.sql_logins WHERE name = N'store_app')
BEGIN
    CREATE LOGIN [store_app]
    WITH PASSWORD = N'ChangeThisStrongPassword!2026',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END;
GO

USE [store_retail_db];
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'store_app')
BEGIN
    CREATE USER [store_app] FOR LOGIN [store_app];
END;
GO

/* Local project convenience. Replace db_owner with narrower permissions before production deployment. */
ALTER ROLE [db_owner] ADD MEMBER [store_app];
GO
