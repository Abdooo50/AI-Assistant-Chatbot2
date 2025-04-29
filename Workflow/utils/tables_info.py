patient_and_doctor_tables_info = \
'''
CREATE TABLE [mosefak-app].[dbo].[ContactUs] (
    [Id] int NOT NULL IDENTITY,
    [Message] nvarchar(256) NOT NULL,
    [AppUserId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    CONSTRAINT [PK_ContactUs] PRIMARY KEY ([Id])
);

CREATE TABLE [mosefak-app].[dbo].[Doctors] (
    [Id] int NOT NULL IDENTITY,
    [AppUserId] int NOT NULL,
    [LicenseNumber] nvarchar(256) NOT NULL,
    [AboutMe] nvarchar(512) NOT NULL,
    [NumberOfReviews] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    CONSTRAINT [PK_Doctors] PRIMARY KEY ([Id])
);

CREATE TABLE [mosefak-app].[dbo].[Notifications] (
    [Id] int NOT NULL IDENTITY,
    [UserId] int NOT NULL,
    [Title] nvarchar(256) NOT NULL,
    [Message] nvarchar(256) NOT NULL,
    [IsRead] bit NOT NULL,
    CONSTRAINT [PK_Notifications] PRIMARY KEY ([Id])
);

CREATE TABLE [mosefak-app].[dbo].[AppointmentTypes] (
    [Id] int NOT NULL IDENTITY,
    [Duration] time NOT NULL,
    [VisitType] nvarchar(256) NOT NULL,
    [ConsultationFee] decimal(10,2) NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_AppointmentTypes] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_AppointmentTypes_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Awards] (
    [Id] int NOT NULL IDENTITY,
    [Title] nvarchar(512) NOT NULL,
    [DateReceived] date NOT NULL,
    [Organization] nvarchar(256) NOT NULL,
    [Description] nvarchar(512) NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
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
    [CreatedAt] datetimeoffset NOT NULL,
    CONSTRAINT [PK_Clinics] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Clinics_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Educations] (
    [Id] int NOT NULL IDENTITY,
    [Degree] nvarchar(256) NOT NULL,
    [Major] nvarchar(256) NOT NULL,
    [UniversityName] nvarchar(256) NOT NULL,
    [UniversityLogoPath] nvarchar(256) NULL,
    [Location] nvarchar(256) NOT NULL,
    [StartDate] date NOT NULL,
    [EndDate] date NULL,
    [CurrentlyStudying] bit NOT NULL,
    [AdditionalNotes] nvarchar(512) NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Educations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Educations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Experiences] (
    [Id] int NOT NULL IDENTITY,
    [Title] nvarchar(256) NOT NULL,
    [HospitalLogo] nvarchar(512) NULL,
    [HospitalName] nvarchar(256) NOT NULL,
    [Location] nvarchar(256) NOT NULL,
    [EmploymentType] int NOT NULL,
    [JobDescription] nvarchar(512) NULL,
    [StartDate] date NOT NULL,
    [EndDate] date NULL,
    [CurrentlyWorkingHere] bit NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Experiences] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Experiences_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Reviews] (
    [Id] int NOT NULL IDENTITY,
    [Rate] int NOT NULL,
    [Comment] nvarchar(256) NULL,
    [AppUserId] int NOT NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    CONSTRAINT [PK_Reviews] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Reviews_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Specializations] (
    [Id] int NOT NULL IDENTITY,
    [Name] nvarchar(max) NOT NULL,
    [Category] nvarchar(max) NOT NULL,
    [DoctorId] int NOT NULL,
    CONSTRAINT [PK_Specializations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Specializations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Appointments] (
    [Id] int NOT NULL IDENTITY,
    [DoctorId] int NOT NULL,
    [PatientId] int NOT NULL,
    [StartDate] datetimeoffset NOT NULL,
    [EndDate] datetimeoffset NOT NULL,
    [AppointmentTypeId] int NOT NULL,
    [ProblemDescription] nvarchar(256) NULL,
    [AppointmentStatus] nvarchar(max) NOT NULL,
    [CancellationReason] nvarchar(256) NULL,
    [PaymentStatus] nvarchar(max) NOT NULL,
    [PaymentDueTime] datetimeoffset NULL,
    [ConfirmedAt] datetimeoffset NULL,
    [CancelledAt] datetimeoffset NULL,
    [CompletedAt] datetimeoffset NULL,
    [ApprovedByDoctor] bit NOT NULL,
    [ServiceProvided] bit NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    CONSTRAINT [PK_Appointments] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Appointments_AppointmentTypes_AppointmentTypeId] FOREIGN KEY ([AppointmentTypeId]) REFERENCES [AppointmentTypes] ([Id]) ON DELETE NO ACTION,
    CONSTRAINT [FK_Appointments_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[WorkingTimes] (
    [Id] int NOT NULL IDENTITY,
    [Day] nvarchar(max) NOT NULL,
    [ClinicId] int NOT NULL,
    CONSTRAINT [PK_WorkingTimes] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_WorkingTimes_Clinics_ClinicId] FOREIGN KEY ([ClinicId]) REFERENCES [Clinics] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Payments] (
    [Id] int NOT NULL IDENTITY,
    [AppointmentId] int NOT NULL,
    [TransactionId] uniqueidentifier NOT NULL,
    [Amount] decimal(10,2) NOT NULL,
    [Status] nvarchar(max) NOT NULL,
    [StripePaymentIntentId] nvarchar(256) NOT NULL,
    [ClientSecret] nvarchar(512) NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    CONSTRAINT [PK_Payments] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Payments_Appointments_AppointmentId] FOREIGN KEY ([AppointmentId]) REFERENCES [Appointments] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Periods] (
    [Id] int NOT NULL IDENTITY,
    [StartTime] TIME NOT NULL,
    [EndTime] TIME NOT NULL,
    [WorkingTimeId] int NOT NULL,
    CONSTRAINT [PK_Periods] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Periods_WorkingTimes_WorkingTimeId] FOREIGN KEY ([WorkingTimeId]) REFERENCES [WorkingTimes] ([Id]) ON DELETE NO ACTION
);

## Private
CREATE TABLE [db18303].[Security].[Roles] (
    [Id] int NOT NULL IDENTITY,
    [CreationTime] datetime2 NOT NULL,
    [IsDeleted] bit NOT NULL,
    [Name] nvarchar(256) NULL,
    [NormalizedName] nvarchar(256) NULL,
    [ConcurrencyStamp] nvarchar(max) NULL,
    CONSTRAINT [PK_Roles] PRIMARY KEY ([Id])
);

## Private
CREATE TABLE [db18303].[Security].[Users] (
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
    [PhoneNumber] nvarchar(max) NULL,
    [PhoneNumberConfirmed] bit NOT NULL,
    [TwoFactorEnabled] bit NOT NULL,
    CONSTRAINT [PK_Users] PRIMARY KEY ([Id])
);


CREATE TABLE [db18303].[Security].[RoleClaims] (
    [Id] int NOT NULL IDENTITY,
    [RoleId] int NOT NULL,
    [ClaimType] nvarchar(max) NULL,
    [ClaimValue] nvarchar(max) NULL,
    CONSTRAINT [PK_RoleClaims] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_RoleClaims_Roles_RoleId] FOREIGN KEY ([RoleId]) REFERENCES [Security].[Roles] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [db18303].[AspNetUserClaims] (
    [Id] int NOT NULL IDENTITY,
    [UserId] int NOT NULL,
    [ClaimType] nvarchar(max) NULL,
    [ClaimValue] nvarchar(max) NULL,
    CONSTRAINT [PK_AspNetUserClaims] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_AspNetUserClaims_Users_UserId] FOREIGN KEY ([UserId]) REFERENCES [Security].[Users] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [db18303].[Security].[UserRoles] (
    [UserId] int NOT NULL,
    [RoleId] int NOT NULL,
    CONSTRAINT [PK_UserRoles] PRIMARY KEY ([UserId], [RoleId]),
    CONSTRAINT [FK_UserRoles_Roles_RoleId] FOREIGN KEY ([RoleId]) REFERENCES [Security].[Roles] ([Id]) ON DELETE CASCADE,
    CONSTRAINT [FK_UserRoles_Users_UserId] FOREIGN KEY ([UserId]) REFERENCES [Security].[Users] ([Id]) ON DELETE CASCADE
);
'''




admin_tables_info = \
'''
CREATE TABLE [mosefak-app].[dbo].[ContactUs] (
    [Id] int NOT NULL IDENTITY,
    [Message] nvarchar(256) NOT NULL,
    [AppUserId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_ContactUs] PRIMARY KEY ([Id])
);

CREATE TABLE [mosefak-app].[dbo].[Doctors] (
    [Id] int NOT NULL IDENTITY,
    [AppUserId] int NOT NULL,
    [LicenseNumber] nvarchar(256) NOT NULL,
    [AboutMe] nvarchar(512) NOT NULL,
    [NumberOfReviews] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Doctors] PRIMARY KEY ([Id])
);

CREATE TABLE [mosefak-app].[dbo].[Notifications] (
    [Id] int NOT NULL IDENTITY,
    [UserId] int NOT NULL,
    [Title] nvarchar(256) NOT NULL,
    [Message] nvarchar(256) NOT NULL,
    [IsRead] bit NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Notifications] PRIMARY KEY ([Id])
);

CREATE TABLE [mosefak-app].[dbo].[AppointmentTypes] (
    [Id] int NOT NULL IDENTITY,
    [Duration] time NOT NULL,
    [VisitType] nvarchar(256) NOT NULL,
    [ConsultationFee] decimal(10,2) NOT NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_AppointmentTypes] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_AppointmentTypes_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Awards] (
    [Id] int NOT NULL IDENTITY,
    [Title] nvarchar(512) NOT NULL,
    [DateReceived] date NOT NULL,
    [Organization] nvarchar(256) NOT NULL,
    [Description] nvarchar(512) NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
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
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Clinics] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Clinics_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Educations] (
    [Id] int NOT NULL IDENTITY,
    [Degree] nvarchar(256) NOT NULL,
    [Major] nvarchar(256) NOT NULL,
    [UniversityName] nvarchar(256) NOT NULL,
    [UniversityLogoPath] nvarchar(256) NULL,
    [Location] nvarchar(256) NOT NULL,
    [StartDate] date NOT NULL,
    [EndDate] date NULL,
    [CurrentlyStudying] bit NOT NULL,
    [AdditionalNotes] nvarchar(512) NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Educations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Educations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Experiences] (
    [Id] int NOT NULL IDENTITY,
    [Title] nvarchar(256) NOT NULL,
    [HospitalLogo] nvarchar(512) NULL,
    [HospitalName] nvarchar(256) NOT NULL,
    [Location] nvarchar(256) NOT NULL,
    [EmploymentType] int NOT NULL,
    [JobDescription] nvarchar(512) NULL,
    [StartDate] date NOT NULL,
    [EndDate] date NULL,
    [CurrentlyWorkingHere] bit NOT NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Experiences] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Experiences_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Reviews] (
    [Id] int NOT NULL IDENTITY,
    [Rate] int NOT NULL,
    [Comment] nvarchar(256) NULL,
    [AppUserId] int NOT NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Reviews] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Reviews_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Specializations] (
    [Id] int NOT NULL IDENTITY,
    [Name] nvarchar(max) NOT NULL,
    [Category] nvarchar(max) NOT NULL,
    [DoctorId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Specializations] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Specializations_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Appointments] (
    [Id] int NOT NULL IDENTITY,
    [DoctorId] int NOT NULL,
    [PatientId] int NOT NULL,
    [StartDate] datetimeoffset NOT NULL,
    [EndDate] datetimeoffset NOT NULL,
    [AppointmentTypeId] int NOT NULL,
    [ProblemDescription] nvarchar(256) NULL,
    [AppointmentStatus] nvarchar(max) NOT NULL,
    [CancellationReason] nvarchar(256) NULL,
    [PaymentStatus] nvarchar(max) NOT NULL,
    [PaymentDueTime] datetimeoffset NULL,
    [ConfirmedAt] datetimeoffset NULL,
    [CancelledAt] datetimeoffset NULL,
    [CompletedAt] datetimeoffset NULL,
    [ApprovedByDoctor] bit NOT NULL,
    [ServiceProvided] bit NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Appointments] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Appointments_AppointmentTypes_AppointmentTypeId] FOREIGN KEY ([AppointmentTypeId]) REFERENCES [AppointmentTypes] ([Id]) ON DELETE NO ACTION,
    CONSTRAINT [FK_Appointments_Doctors_DoctorId] FOREIGN KEY ([DoctorId]) REFERENCES [Doctors] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[WorkingTimes] (
    [Id] int NOT NULL IDENTITY,
    [Day] nvarchar(max) NOT NULL,
    [ClinicId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_WorkingTimes] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_WorkingTimes_Clinics_ClinicId] FOREIGN KEY ([ClinicId]) REFERENCES [Clinics] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Payments] (
    [Id] int NOT NULL IDENTITY,
    [AppointmentId] int NOT NULL,
    [TransactionId] uniqueidentifier NOT NULL,
    [Amount] decimal(10,2) NOT NULL,
    [Status] nvarchar(max) NOT NULL,
    [StripePaymentIntentId] nvarchar(256) NOT NULL,
    [ClientSecret] nvarchar(512) NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Payments] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Payments_Appointments_AppointmentId] FOREIGN KEY ([AppointmentId]) REFERENCES [Appointments] ([Id]) ON DELETE NO ACTION
);

CREATE TABLE [mosefak-app].[dbo].[Periods] (
    [Id] int NOT NULL IDENTITY,
    [StartTime] TIME NOT NULL,
    [EndTime] TIME NOT NULL,
    [WorkingTimeId] int NOT NULL,
    [CreatedAt] datetimeoffset NOT NULL,
    [CreatedByUserId] int NOT NULL,
    [FirstUpdatedTime] datetimeoffset NULL,
    [LastUpdatedTime] datetimeoffset NULL,
    [FirstUpdatedByUserId] int NULL,
    [LastUpdatedByUserId] int NULL,
    [IsDeleted] bit NOT NULL,
    [DeletedTime] datetimeoffset NULL,
    [DeletedByUserId] int NULL,
    CONSTRAINT [PK_Periods] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_Periods_WorkingTimes_WorkingTimeId] FOREIGN KEY ([WorkingTimeId]) REFERENCES [WorkingTimes] ([Id]) ON DELETE NO ACTION
);

## Private
CREATE TABLE [db18303].[Security].[Roles] (
    [Id] int NOT NULL IDENTITY,
    [CreationTime] datetime2 NOT NULL,
    [IsDeleted] bit NOT NULL,
    [Name] nvarchar(256) NULL,
    [NormalizedName] nvarchar(256) NULL,
    [ConcurrencyStamp] nvarchar(max) NULL,
    CONSTRAINT [PK_Roles] PRIMARY KEY ([Id])
);

## Private
CREATE TABLE [db18303].[Security].[Users] (
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


CREATE TABLE [db18303].[Security].[RoleClaims] (
    [Id] int NOT NULL IDENTITY,
    [RoleId] int NOT NULL,
    [ClaimType] nvarchar(max) NULL,
    [ClaimValue] nvarchar(max) NULL,
    CONSTRAINT [PK_RoleClaims] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_RoleClaims_Roles_RoleId] FOREIGN KEY ([RoleId]) REFERENCES [Security].[Roles] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [db18303].[AspNetUserClaims] (
    [Id] int NOT NULL IDENTITY,
    [UserId] int NOT NULL,
    [ClaimType] nvarchar(max) NULL,
    [ClaimValue] nvarchar(max) NULL,
    CONSTRAINT [PK_AspNetUserClaims] PRIMARY KEY ([Id]),
    CONSTRAINT [FK_AspNetUserClaims_Users_UserId] FOREIGN KEY ([UserId]) REFERENCES [Security].[Users] ([Id]) ON DELETE CASCADE
);

CREATE TABLE [db18303].[Security].[UserRoles] (
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
