CREATE TABLE `settings` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
	`value` TEXT NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

INSERT INTO settings (`id`, `name`, `value`) VALUES (1, 'LOGS', '{"local":{},"amazon_s3":{}}'), (2, 'SECURITY', '{"url":""}');

CREATE TABLE `groups` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) NOT NULL,
  `description` text,
  `coins_day` INT UNSIGNED NOT NULL DEFAULT '25',
  `coins_max` INT UNSIGNED NOT NULL DEFAULT '100',
  `coins_execution` INT UNSIGNED NOT NULL DEFAULT '10',
  `inventory_enable` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_enable` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_basic` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_pro` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_inbenta` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_execution_threads` tinyint(255) UNSIGNED NOT NULL DEFAULT '10',
  `deployments_execution_limit` INT UNSIGNED NULL,
  `deployments_execution_concurrent` INT UNSIGNED NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `users` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `coins` INT UNSIGNED NOT NULL DEFAULT '0',
  `group_id` int(10) unsigned NOT NULL,
  `admin` tinyint(1) NOT NULL DEFAULT '0',
  `last_login` DATETIME NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `group_id` (`group_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `environments` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id__name` (`group_id`,`name`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `regions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `ssh_tunnel` tinyint(1) NOT NULL,
  `hostname` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `port` INT UNSIGNED DEFAULT NULL,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `key` text COLLATE utf8mb4_unicode_ci,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id__name` (`group_id`,`name`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `servers` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `engine` enum('MySQL','PostgreSQL') COLLATE utf8mb4_unicode_ci NOT NULL,
  `region_id` int(10) unsigned NOT NULL,
  `hostname` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `port` INT UNSIGNED NOT NULL,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `region_id__name` (`region_id`,`name`),
  FOREIGN KEY (`region_id`) REFERENCES `regions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `environment_servers` (
  `environment_id` int(10) unsigned NOT NULL,
  `server_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`environment_id`, `server_id`),
  INDEX `server_id` (`server_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `auxiliary` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `ssh_tunnel` tinyint(1) NOT NULL,
  `ssh_hostname` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ssh_port` INT UNSIGNED DEFAULT NULL,
  `ssh_username` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ssh_password` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ssh_key` text COLLATE utf8mb4_unicode_ci,
  `sql_engine` enum('MySQL','PostgreSQL') COLLATE utf8mb4_unicode_ci NOT NULL,
  `sql_hostname` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sql_port` INT UNSIGNED NOT NULL,
  `sql_username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sql_password` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id__name` (`group_id`,`name`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `slack` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `channel_name` varchar(191) COLLATE utf8mb4_unicode_ci,
  `webhook_url` text COLLATE utf8mb4_unicode_ci,
  `enabled` tinyint(1) DEFAULT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `releases` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `active` TINYINT(1) NOT NULL DEFAULT 1,
  `user_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id__name` (`user_id`, `name`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments` (
  `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `release_id` INT UNSIGNED NULL,
  `user_id` INT(10) UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  KEY `release_id` (`release_id`),
  KEY `user_id` (`user_id`),
  FOREIGN KEY (`release_id`) REFERENCES `releases` (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_basic` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `deployment_id` INT UNSIGNED NOT NULL,
 `environment_id` INT(10) UNSIGNED NOT NULL,
 `databases` TEXT NOT NULL,
 `queries` TEXT NOT NULL,
 `method` ENUM('VALIDATE','TEST','DEPLOY') NOT NULL,
 `status` ENUM('CREATED','SCHEDULED','QUEUED','STARTING','IN PROGRESS','SUCCESS','WARNING','FAILED','STOPPING','STOPPED') NOT NULL DEFAULT 'CREATED',
 `created` DATETIME NOT NULL,
 `scheduled` DATETIME NULL,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `progress` TEXT NULL,
 `error` TINYINT(1) NULL,
 `uri` VARCHAR(191) NULL,
 `engine` VARCHAR(191) NULL,
 `public` TINYINT(1) NOT NULL DEFAULT 0,
 `expired` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `deployment_id` (`deployment_id`),
  KEY `status` (`status`),
  KEY `scheduled` (`scheduled`),
  KEY `uri` (`uri`),
  KEY `created` (`created`),
  KEY `expired` (`expired`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`),
  FOREIGN KEY (`environment_id`) REFERENCES `environments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_pro` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `deployment_id` INT UNSIGNED NOT NULL,
 `environment_id` INT(10) UNSIGNED NOT NULL,
 `code` MEDIUMTEXT NOT NULL,
 `method` ENUM('VALIDATE','TEST','DEPLOY') NOT NULL,
 `status` ENUM('CREATED','SCHEDULED','QUEUED','STARTING','IN PROGRESS','SUCCESS','WARNING','FAILED','STOPPING','STOPPED') NOT NULL DEFAULT 'CREATED',
 `created` DATETIME NOT NULL,
 `scheduled` DATETIME NULL,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `progress` TEXT NULL,
 `error` TINYINT(1) NULL,
 `uri` VARCHAR(191) NULL,
 `engine` VARCHAR(191) NULL,
 `public` TINYINT(1) NOT NULL DEFAULT 0,
 `expired` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY(id),
  KEY `deployment_id` (`deployment_id`),
  KEY `status` (`status`),
  KEY `scheduled` (`scheduled`),
  KEY `uri` (`uri`),
  KEY `created` (`created`),
  KEY `expired` (`expired`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`),
  FOREIGN KEY (`environment_id`) REFERENCES `environments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_inbenta` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `deployment_id` INT UNSIGNED NOT NULL,
 `environment_id` INT(10) UNSIGNED NOT NULL,
 `products` SET('chatbot','km','no-product','search','ticketing') NOT NULL,
 `schema` VARCHAR(191) NOT NULL,
 `databases` TEXT NULL,
 `queries` TEXT NOT NULL,
 `method` ENUM('VALIDATE','TEST','DEPLOY') NOT NULL,
 `status` ENUM('CREATED','SCHEDULED','QUEUED','STARTING','IN PROGRESS','SUCCESS','WARNING','FAILED','STOPPING','STOPPED') NOT NULL DEFAULT 'CREATED',
 `created` DATETIME NOT NULL,
 `scheduled` DATETIME NULL,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `progress` TEXT NULL,
 `error` TINYINT(1) NULL,
 `uri` VARCHAR(191) NULL,
 `engine` VARCHAR(191) NULL,
 `public` TINYINT(1) NOT NULL DEFAULT 0,
 `expired` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `deployment_id` (`deployment_id`),
  KEY `status` (`status`),
  KEY `scheduled` (`scheduled`),
  KEY `uri` (`uri`),
  KEY `created` (`created`),
  KEY `expired` (`expired`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`),
  FOREIGN KEY (`environment_id`) REFERENCES `environments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_queued` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT,
  `execution_mode` VARCHAR(191) NOT NULL COMMENT 'References [deployments_basic, deployments_pro].mode',
  `execution_id` INT UNSIGNED NOT NULL COMMENT 'References [deployments_basic, deployments_pro].id',
  PRIMARY KEY (`id`),
  UNIQUE uniq (`execution_mode`, `execution_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_finished` (
  `deployment_mode` VARCHAR(191) NOT NULL COMMENT 'References [deployments_basic, deployments_pro].mode',
  `deployment_id` INT UNSIGNED NOT NULL COMMENT 'References [deployments_basic, deployments_pro].id',
  PRIMARY KEY (`deployment_mode`, `deployment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `notifications` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `status` ENUM('INFO','SUCCESS','WARNING','ERROR') NOT NULL,
  `icon` VARCHAR(191) NULL,
  `category` VARCHAR(191) NOT NULL,
  `data` TEXT NOT NULL,
  `date` DATETIME NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  `show` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `category` (`category`),
  KEY `user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;