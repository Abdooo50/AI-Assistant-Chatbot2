patient_and_doctor_tables_info = \
'''
CREATE TABLE [mosefak-app].[dbo].[Doctors] (
    [Id] int NOT NULL IDENTITY,
    [AppUserId] int NOT NULL,
    [YearOfExperience] int NOT NULL,
    [LicenseNumber] nvarchar(max) NOT NULL,
    [AboutMe] nvarchar(max) NOT NULL,
    [NumberOfReviews] int NOT NULL,
    [ConsultationFee] decimal(18,2) NOT NULL,
    CONSTRAINT [PK_Doctors] PRIMARY KEY ([Id])
);

CREATE TABLE [mosefak-app].[dbo].[Appointments] (
    [Id] int NOT NULL,
    [DoctorId] int NOT NULL,
    [AppUserId] int NOT NULL,
    [StartDate] datetime2 NOT NULL,
    [EndDate] datetime2 NOT NULL,
    [ProblemDescription] nvarchar(max) NOT NULL,
    [AppointmentStatus] nvarchar(max) NOT NULL,
    [CancellationReason] nvarchar(max) NULL,
    [IsPaid] bit NOT NULL,
    CONSTRAINT [PK_Appointments] PRIMARY KEY ([Id], [AppUserId], [DoctorId]),
    CONSTRAINT [FK_Appointments_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [mosefak-app].[dbo].[Clinics] (
    [Id] int NOT NULL IDENTITY,
    [Street] nvarchar(max) NOT NULL,
    [City] nvarchar(max) NOT NULL,
    [Country] nvarchar(max) NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_ClinicAddresses] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_ClinicAddresses_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [mosefak-app].[dbo].[Reviews] (
    [Id] int NOT NULL IDENTITY,
    [Rate] int NOT NULL,
    [Comment] nvarchar(max) NULL,
    [AppUserId] int NOT NULL,
    [DoctorId] int NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Reviews] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Reviews_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id])
);

CREATE TABLE [mosefak-app].[dbo].[Specializations] (
    [Id] int NOT NULL IDENTITY,
    [Name] int NOT NULL,
    [Category] int NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Specializations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Specializations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [mosefak-app].[dbo].[WorkingTimes] (
    [Id] int NOT NULL IDENTITY,
    [ClinicId] int NOT NULL,
    [Day] nvarchar(max) NOT NULL,
    CONSTRAINT [PK_WorkingTimes] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_WorkingTimes_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [mosefak-app].[dbo].[Payments] (
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
    CONSTRAINT [PK_Payments] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Payments_Appointments_AppointmentId_AppointmentAppUserId_AppointmentDoctorId] FOREIGN KEY ([AppointmentId], [AppointmentAppUserId], [AppointmentDoctorId]) REFERENCES [Appointments] ([Id], [AppUserId], [DoctorId]) ON DELETE CASCADE
);


CREATE TABLE [mosefak-app].[dbo].[Awards] (
    [Id] int NOT NULL IDENTITY,
    [Title] nvarchar(max) NOT NULL,
    [DateReceived] date NOT NULL,
    [Organization] nvarchar(max) NOT NULL,
    [Description] nvarchar(max) NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Awards] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Awards_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Clinics] (
    [Id] int NOT NULL IDENTITY,
    [Name] nvarchar(max) NOT NULL,
    [Street] nvarchar(max) NOT NULL,
    [City] nvarchar(max) NOT NULL,
    [Country] nvarchar(max) NOT NULL,
    [ApartmentOrSuite] nvarchar(max) NOT NULL,
    [Landmark] nvarchar(max) NOT NULL,
    [LogoPath] nvarchar(max) NULL,
    [ClinicImage] nvarchar(max) NULL,
    [PhoneNumber] nvarchar(max) NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Clinics] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Clinics_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Educations] (
    [Id] int NOT NULL IDENTITY,
    [Degree] nvarchar(max) NOT NULL,
    [Major] nvarchar(max) NOT NULL,
    [UniversityName] nvarchar(max) NOT NULL,
    [UniversityLogoPath] nvarchar(max) NULL,
    [Location] nvarchar(max) NOT NULL,
    [StartDate] date NOT NULL,
    [EndDate] date NULL,
    [CurrentlyStudying] bit NOT NULL,
    [AdditionalNotes] nvarchar(max) NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Educations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Educations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Experiences] (
    [Id] int NOT NULL IDENTITY,
    [Title] nvarchar(max) NOT NULL,
    [HospitalLogo] nvarchar(max) NULL,
    [HospitalName] nvarchar(max) NOT NULL,
    [Location] nvarchar(max) NOT NULL,
    [EmploymentType] int NOT NULL,
    [JobDescription] nvarchar(max) NULL,
    [StartDate] date NOT NULL,
    [EndDate] date NULL,
    [CurrentlyWorkingHere] bit NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Experiences] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Experiences_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Periods] (
    [Id] int NOT NULL IDENTITY,
    [StartTime] TIME NOT NULL,
    [EndTime] TIME NOT NULL,
    [WorkingTimeId] int NOT NULL,
    CONSTRAINT [PK_Periods] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Periods_WorkingTimes_WorkingTimeId] FOREIGN KEY ([WorkingTimeId]) REFERENCES [WorkingTimes] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-management].[Security].[Roles] (
    [Id] int NOT NULL IDENTITY,
    [CreationTime] datetime2 NOT NULL,
    [IsDeleted] bit NOT NULL,
    [Name] nvarchar(256) NULL,
    [NormalizedName] nvarchar(256) NULL,
    [ConcurrencyStamp] nvarchar(max) NULL,
    CONSTRAINT [PK_Roles] PRIMARY KEY ([Id])
);


CREATE TABLE [mosefak-management].[Security].[Users] (
    [Id] int NOT NULL IDENTITY,
    [FirstName] nvarchar(250) NOT NULL,
    [LastName] nvarchar(250) NOT NULL,
    [Gender] nvarchar(max) NULL,
    [Address_Id] int NOT NULL,
    [Address_City] nvarchar(max) NOT NULL,
    [Address_Street] nvarchar(max) NOT NULL,
    [DateOfBirth] datetime2 NULL,
    [UserName] nvarchar(256) NULL,
    [Email] nvarchar(256) NULL,
    [EmailConfirmed] bit NOT NULL,
    [PhoneNumber] nvarchar(max) NULL,
    [PhoneNumberConfirmed] bit NOT NULL,
    [TwoFactorEnabled] bit NOT NULL,
    CONSTRAINT [PK_Users] PRIMARY KEY ([Id])
);
'''




admin_tables_info = \
'''
CREATE TABLE [mosefak-app].[dbo].[Awards] (
    [Id] int NOT NULL IDENTITY,
    [Title] nvarchar(max) NOT NULL,
    [DateReceived] date NOT NULL,
    [Organization] nvarchar(max) NOT NULL,
    [Description] nvarchar(max) NULL,
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
    CONSTRAINT [PK_Awards] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Awards_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Clinics] (
    [Id] int NOT NULL IDENTITY,
    [Name] nvarchar(max) NOT NULL,
    [Street] nvarchar(max) NOT NULL,
    [City] nvarchar(max) NOT NULL,
    [Country] nvarchar(max) NOT NULL,
    [ApartmentOrSuite] nvarchar(max) NOT NULL,
    [Landmark] nvarchar(max) NOT NULL,
    [LogoPath] nvarchar(max) NULL,
    [ClinicImage] nvarchar(max) NULL,
    [PhoneNumber] nvarchar(max) NOT NULL,
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
    CONSTRAINT [PK_Clinics] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Clinics_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [Educations] (
    [Id] int NOT NULL IDENTITY,
    [Degree] nvarchar(max) NOT NULL,
    [Major] nvarchar(max) NOT NULL,
    [UniversityName] nvarchar(max) NOT NULL,
    [UniversityLogoPath] nvarchar(max) NULL,
    [Location] nvarchar(max) NOT NULL,
    [StartDate] date NOT NULL,
    [EndDate] date NULL,
    [CurrentlyStudying] bit NOT NULL,
    [AdditionalNotes] nvarchar(max) NULL,
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
    CONSTRAINT [PK_Educations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Educations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [Experiences] (
    [Id] int NOT NULL IDENTITY,
    [Title] nvarchar(max) NOT NULL,
    [HospitalLogo] nvarchar(max) NULL,
    [HospitalName] nvarchar(max) NOT NULL,
    [Location] nvarchar(max) NOT NULL,
    [EmploymentType] int NOT NULL,
    [JobDescription] nvarchar(max) NULL,
    [StartDate] date NOT NULL,
    [EndDate] date NULL,
    [CurrentlyWorkingHere] bit NOT NULL,
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
    CONSTRAINT [PK_Experiences] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Experiences_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [Periods] (
    [Id] int NOT NULL IDENTITY,
    [StartTime] TIME NOT NULL,
    [EndTime] TIME NOT NULL,
    [WorkingTimeId] int NOT NULL,
    [CreatedAt] datetime2 NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetime2 NULL,
    [LastUpdatedTime] datetime2 NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetime2 NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Periods] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Periods_WorkingTimes_WorkingTimeId] FOREIGN KEY ([WorkingTimeId]) REFERENCES [WorkingTimes] ([Id]) ON DELETE NO ACTION
);
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
    [Name] int NOT NULL,
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

## Private
CREATE TABLE [Security].[Roles] (
    [Id] int NOT NULL IDENTITY,
    [CreationTime] datetime2 NOT NULL,
    [IsDeleted] bit NOT NULL,
    [Name] nvarchar(256) NULL,
    [NormalizedName] nvarchar(256) NULL,
    [ConcurrencyStamp] nvarchar(max) NULL,
    CONSTRAINT [PK_Roles] PRIMARY KEY ([Id])
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
'''


def load_tables_info(role: str):

    if role in ["Patient", "Doctor"]:
        return patient_and_doctor_tables_info
    else:
        return admin_tables_info
