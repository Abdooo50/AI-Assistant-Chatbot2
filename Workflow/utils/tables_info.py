patient_and_doctor_tables_info = \
'''
CREATE TABLE [Doctors] (
    [Id] int NOT NULL IDENTITY,
    [AppUserId] int NOT NULL,
    [YearOfExperience] int NOT NULL,
    [AboutMe] nvarchar(max) NOT NULL,
    [NumberOfReviews] int NOT NULL,
    [ConsultationFee] decimal(18,2) NOT NULL,
    CONSTRAINT [PK_Doctors] PRIMARY KEY ([Id])
);

CREATE TABLE [Appointments] (
    [Id] int NOT NULL,
    [DoctorId] int NOT NULL,
    [AppUserId] int NOT NULL,
    [StartDate] datetime2 NOT NULL,
    [EndDate] datetime2 NOT NULL,
    [ProblemDescription] nvarchar(max) NOT NULL, ## Private
    [AppointmentStatus] nvarchar(max) NOT NULL,
    [CancellationReason] nvarchar(max) NULL, ## Private
    [IsPaid] bit NOT NULL, ## Private
    CONSTRAINT [PK_Appointments] PRIMARY KEY ([Id], [AppUserId], [DoctorId]),
    CONSTRAINT [FK_Appointments_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [ClinicAddresses] (
    [Id] int NOT NULL IDENTITY,
    [Street] nvarchar(max) NOT NULL,
    [City] nvarchar(max) NOT NULL,
    [Country] nvarchar(max) NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_ClinicAddresses] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_ClinicAddresses_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [Reviews] (
    [Id] int NOT NULL IDENTITY,
    [Rate] int NOT NULL,
    [Comment] nvarchar(max) NULL,
    [AppUserId] int NOT NULL,
    [DoctorId] int NULL,
    CONSTRAINT [PK_Reviews] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Reviews_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id])
);

CREATE TABLE [Specializations] (
    [Id] int NOT NULL IDENTITY,
    [Name] nvarchar(max) NOT NULL,
    [Category] int NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Specializations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Specializations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [WorkingTimes] (
    [Id] int NOT NULL IDENTITY,
    [DoctorId] int NOT NULL,
    [DayOfWeek] nvarchar(max) NOT NULL,
    [StartTime] TIME NOT NULL,
    [EndTime] TIME NOT NULL,
    CONSTRAINT [PK_WorkingTimes] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_WorkingTimes_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

## Private
CREATE TABLE [Security].[Users] (
    [Id] int NOT NULL IDENTITY,
    [FirstName] nvarchar(250) NOT NULL,
    [LastName] nvarchar(250) NOT NULL,
    [Gender] nvarchar(max) NULL,
    [Address_Id] int NOT NULL,
    [Address_State] nvarchar(max) NOT NULL,
    [Address_City] nvarchar(max) NOT NULL,
    [Address_Street] nvarchar(max) NOT NULL,
    [Address_ZipCode] int NOT NULL,
    [DateOfBirth] datetime2 NULL,
    [ImagePath] nvarchar(max) NULL,
    [CreationTime] datetime2 NOT NULL,
    [UserName] nvarchar(256) NULL,
    [Email] nvarchar(256) NULL,
    [EmailConfirmed] bit NOT NULL,
    [ConcurrencyStamp] nvarchar(max) NULL,
    [PhoneNumber] nvarchar(max) NULL,
    [PhoneNumberConfirmed] bit NOT NULL,
    [TwoFactorEnabled] bit NOT NULL,
    CONSTRAINT [PK_Users] PRIMARY KEY ([Id])
);
'''




admin_tables_info = \
'''
CREATE TABLE [Doctors] (
    [Id] int NOT NULL IDENTITY,
    [AppUserId] int NOT NULL,
    [YearOfExperience] int NOT NULL,
    [LicenseNumber] nvarchar(max) NOT NULL,
    [AboutMe] nvarchar(max) NOT NULL,
    [NumberOfReviews] int NOT NULL,
    [ConsultationFee] decimal(18,2) NOT NULL,
    [CreatedAt] datetime2 NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetime2 NULL,
    [LastUpdatedTime] datetime2 NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetime2 NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Doctors] PRIMARY KEY ([Id])
);

CREATE TABLE [Appointments] (
    [Id] int NOT NULL,
    [DoctorId] int NOT NULL,
    [AppUserId] int NOT NULL,
    [StartDate] datetime2 NOT NULL,
    [EndDate] datetime2 NOT NULL,
    [ProblemDescription] nvarchar(max) NOT NULL,
    [AppointmentStatus] nvarchar(max) NOT NULL,
    [CancellationReason] nvarchar(max) NULL,
    [IsPaid] bit NOT NULL,
    [CreatedAt] datetime2 NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetime2 NULL,
    [LastUpdatedTime] datetime2 NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetime2 NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Appointments] PRIMARY KEY ([Id], [AppUserId], [DoctorId]),
    CONSTRAINT [FK_Appointments_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [ClinicAddresses] (
    [Id] int NOT NULL IDENTITY,
    [Street] nvarchar(max) NOT NULL,
    [City] nvarchar(max) NOT NULL,
    [Country] nvarchar(max) NOT NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetime2 NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetime2 NULL,
    [LastUpdatedTime] datetime2 NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetime2 NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_ClinicAddresses] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_ClinicAddresses_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [Reviews] (
    [Id] int NOT NULL IDENTITY,
    [Rate] int NOT NULL,
    [Comment] nvarchar(max) NULL,
    [AppUserId] int NOT NULL,
    [DoctorId] int NULL,
    [CreatedAt] datetime2 NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetime2 NULL,
    [LastUpdatedTime] datetime2 NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetime2 NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Reviews] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Reviews_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id])
);

CREATE TABLE [Specializations] (
    [Id] int NOT NULL IDENTITY,
    [Name] nvarchar(max) NOT NULL,
    [Category] int NOT NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetime2 NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetime2 NULL,
    [LastUpdatedTime] datetime2 NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetime2 NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Specializations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Specializations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [WorkingTimes] (
    [Id] int NOT NULL IDENTITY,
    [DoctorId] int NOT NULL,
    [DayOfWeek] nvarchar(max) NOT NULL,
    [StartTime] TIME NOT NULL,
    [EndTime] TIME NOT NULL,
    [CreatedAt] datetime2 NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetime2 NULL,
    [LastUpdatedTime] datetime2 NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetime2 NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_WorkingTimes] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_WorkingTimes_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [Payments] (
    [Id] int NOT NULL IDENTITY,
    [Amount] decimal(18,2) NOT NULL,
    [Currency] nvarchar(max) NOT NULL,
    [PaymentMethod] nvarchar(max) NOT NULL,
    [PaymentDate] datetime2 NOT NULL,
    [TransactionId] nvarchar(max) NOT NULL,
    [IsSuccessful] bit NOT NULL,
    [PaymentIntentId] nvarchar(max) NOT NULL,
    [ClientSecret] nvarchar(max) NOT NULL,
    [AppointmentId] int NOT NULL,
    [AppointmentAppUserId] int NOT NULL,
    [AppointmentDoctorId] int NOT NULL,
    [PatientId] int NOT NULL,
    [CreatedAt] datetime2 NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetime2 NULL,
    [LastUpdatedTime] datetime2 NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetime2 NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Payments] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Payments_Appointments_AppointmentId_AppointmentAppUserId_AppointmentDoctorId] FOREIGN KEY ([AppointmentId], [AppointmentAppUserId], [AppointmentDoctorId]) REFERENCES [Appointments] ([Id], [AppUserId], [DoctorId]) ON DELETE CASCADE
);


BEGIN TRANSACTION;
IF SCHEMA_ID(N'Security') IS NULL EXEC(N'CREATE SCHEMA [Security];');

CREATE TABLE [Security].[Roles] (
    [Id] int NOT NULL IDENTITY,
    [CreationTime] datetime2 NOT NULL,
    [IsDeleted] bit NOT NULL,
    [Name] nvarchar(256) NULL,
    [NormalizedName] nvarchar(256) NULL,
    [ConcurrencyStamp] nvarchar(max) NULL,
    CONSTRAINT [PK_Roles] PRIMARY KEY ([Id])
);

CREATE TABLE [Security].[Users] (
    [Id] int NOT NULL IDENTITY,
    [FirstName] nvarchar(250) NOT NULL,
    [LastName] nvarchar(250) NOT NULL,
    [Gender] nvarchar(max) NULL,
    [Address_Id] int NOT NULL,
    [Address_State] nvarchar(max) NOT NULL,
    [Address_City] nvarchar(max) NOT NULL,
    [Address_Street] nvarchar(max) NOT NULL,
    [Address_ZipCode] int NOT NULL,
    [DateOfBirth] datetime2 NULL,
    [ImagePath] nvarchar(max) NULL,
    [CreationTime] datetime2 NOT NULL,
    [IsDeleted] bit NOT NULL,
    [IsDisabled] bit NOT NULL,
    [UserName] nvarchar(256) NULL,
    [NormalizedUserName] nvarchar(256) NULL,
    [Email] nvarchar(256) NULL,
    [NormalizedEmail] nvarchar(256) NULL,
    [EmailConfirmed] bit NOT NULL,
    [PasswordHash] nvarchar(max) NULL,
    [SecurityStamp] nvarchar(max) NULL,
    [ConcurrencyStamp] nvarchar(max) NULL,
    [PhoneNumber] nvarchar(max) NULL,
    [PhoneNumberConfirmed] bit NOT NULL,
    [TwoFactorEnabled] bit NOT NULL,
    [LockoutEnd] datetimeoffset NULL,
    [LockoutEnabled] bit NOT NULL,
    [AccessFailedCount] int NOT NULL,
    CONSTRAINT [PK_Users] PRIMARY KEY ([Id])
);

CREATE TABLE [Security].[RoleClaims] (
    [Id] int NOT NULL IDENTITY,
    [RoleId] int NOT NULL,
    [ClaimType] nvarchar(max) NULL,
    [ClaimValue] nvarchar(max) NULL,
    CONSTRAINT [PK_RoleClaims] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_RoleClaims_Roles_RoleId] FOREIGN KEY ([RoleId]) REFERENCES [Security].[Roles] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [AspNetUserClaims] (
    [Id] int NOT NULL IDENTITY,
    [UserId] int NOT NULL,
    [ClaimType] nvarchar(max) NULL,
    [ClaimValue] nvarchar(max) NULL,
    CONSTRAINT [PK_AspNetUserClaims] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_AspNetUserClaims_Users_UserId] FOREIGN KEY ([UserId]) REFERENCES [Security].[Users] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [AspNetUserLogins] (
    [LoginProvider] nvarchar(450) NOT NULL,
    [ProviderKey] nvarchar(450) NOT NULL,
    [ProviderDisplayName] nvarchar(max) NULL,
    [UserId] int NOT NULL,
    CONSTRAINT [PK_AspNetUserLogins] PRIMARY KEY ([LoginProvider], [ProviderKey]),
    CONSTRAINT [FK_AspNetUserLogins_Users_UserId] FOREIGN KEY ([UserId]) REFERENCES [Security].[Users] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [AspNetUserTokens] (
    [UserId] int NOT NULL,
    [LoginProvider] nvarchar(450) NOT NULL,
    [Name] nvarchar(450) NOT NULL,
    [Value] nvarchar(max) NULL,
    CONSTRAINT [PK_AspNetUserTokens] PRIMARY KEY ([UserId], [LoginProvider], [Name]),
    CONSTRAINT [FK_AspNetUserTokens_Users_UserId] FOREIGN KEY ([UserId]) REFERENCES [Security].[Users] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [Security].[UserRoles] (
    [UserId] int NOT NULL,
    [RoleId] int NOT NULL,
    CONSTRAINT [PK_UserRoles] PRIMARY KEY ([UserId], [RoleId]),
    CONSTRAINT [FK_UserRoles_Roles_RoleId] FOREIGN KEY ([RoleId]) REFERENCES [Security].[Roles] ([Id]) ON DELETE CASCADE,
    CONSTRAINT [FK_UserRoles_Users_UserId] FOREIGN KEY ([UserId]) REFERENCES [Security].[Users] ([Id]) ON DELETE CASCADE
);
);
'''


def load_tables_info(role: str):

    if role in ["Patient", "Doctor"]:
        return patient_and_doctor_tables_info
    else:
        return admin_tables_info
