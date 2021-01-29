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
  `inventory_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `inventory_secured` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_basic` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_pro` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_execution_threads` tinyint(255) UNSIGNED NOT NULL DEFAULT '10',
  `deployments_execution_timeout` INT UNSIGNED NULL,
  `deployments_execution_concurrent` INT UNSIGNED NULL,
  `deployments_slack_enabled` TINYINT(1) NOT NULL DEFAULT '0',
  `deployments_slack_name` VARCHAR(191) NULL,
  `deployments_slack_url` VARCHAR(191) NULL,
  `monitoring_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `utils_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `client_enabled` tinyint(1) NOT NULL DEFAULT '0',
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
  `mfa` TINYINT(1) NOT NULL DEFAULT '0',
  `mfa_hash` varchar(191) NULL,
  `email` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `coins` INT UNSIGNED NOT NULL DEFAULT '0',
  `group_id` int(10) unsigned NOT NULL,
  `admin` tinyint(1) NOT NULL DEFAULT '0',
  `disabled` TINYINT(1) NOT NULL DEFAULT '0',
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

CREATE TABLE `group_owners` (
  `group_id` int(10) unsigned NOT NULL,
  `user_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`group_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `environments` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `shared` tinyint(1) NOT NULL,
  `owner_id` int(10) unsigned NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  INDEX `name` (`name`),
  INDEX `group_id` (`group_id`),
  INDEX `shared` (`shared`),
  INDEX `owner_id` (`owner_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`)
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
  `shared` tinyint(1) NOT NULL,
  `owner_id` int(10) unsigned NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  INDEX `name` (`name`),
  INDEX `group_id` (`group_id`),
  INDEX `shared` (`shared`),
  INDEX `owner_id` (`owner_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `servers` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `region_id` int(10) unsigned NULL,
  `engine` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hostname` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `port` INT UNSIGNED NOT NULL,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ssl` tinyint(1) NOT NULL,
  `ssl_client_key` text COLLATE utf8mb4_unicode_ci,
  `ssl_client_certificate` text COLLATE utf8mb4_unicode_ci,
  `ssl_ca_certificate` text COLLATE utf8mb4_unicode_ci,
  `usage` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shared` tinyint(1) NOT NULL,
  `owner_id` int(10) unsigned NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  INDEX `name` (`name`),
  INDEX `group_id` (`group_id`),
  INDEX `shared` (`shared`),
  INDEX `owner_id` (`owner_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  FOREIGN KEY (`region_id`) REFERENCES `regions` (`id`),
  FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`)
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
  `sql_engine`  varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sql_version`  varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sql_hostname` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sql_port` INT UNSIGNED NOT NULL,
  `sql_username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sql_password` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sql_ssl` tinyint(1) NOT NULL,
  `sql_ssl_client_key` text COLLATE utf8mb4_unicode_ci,
  `sql_ssl_client_certificate` text COLLATE utf8mb4_unicode_ci,
  `sql_ssl_ca_certificate` text COLLATE utf8mb4_unicode_ci,
  `shared` tinyint(1) NOT NULL,
  `owner_id` int(10) unsigned NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  INDEX `name` (`name`),
  INDEX `group_id` (`group_id`),
  INDEX `shared` (`shared`),
  INDEX `owner_id` (`owner_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `releases` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `active` TINYINT(1) NOT NULL DEFAULT 1,
  `user_id` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id|name` (`user_id`, `name`),
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
 `stopped` ENUM('graceful','forceful') NULL,
 `created` DATETIME NOT NULL,
 `scheduled` DATETIME NULL,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `progress` TEXT NULL,
 `error` TINYINT(1) NULL,
 `url` VARCHAR(191) NULL,
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
 `stopped` ENUM('graceful','forceful') NULL,
 `created` DATETIME NOT NULL,
 `scheduled` DATETIME NULL,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `progress` TEXT NULL,
 `error` TINYINT(1) NULL,
 `url` VARCHAR(191) NULL,
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
  `data` TEXT NULL,
  `date` DATETIME NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  `show` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `category` (`category`),
  KEY `user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `monitoring` (
  `user_id` INT UNSIGNED NOT NULL,
  `server_id` INT UNSIGNED NOT NULL,
  `monitor_enabled` TINYINT(1) NOT NULL DEFAULT 0,
	`parameters_enabled` TINYINT(1) NOT NULL DEFAULT 0,
	`processlist_enabled` TINYINT(1) NOT NULL DEFAULT 0,
  `processlist_active` TINYINT(1) NOT NULL DEFAULT 0,
	`queries_enabled` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`user_id`, `server_id`),
  INDEX (`server_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `monitoring_settings` (
  `user_id` INT UNSIGNED NOT NULL,
	`monitor_align` TINYINT UNSIGNED NOT NULL DEFAULT 4,
  `monitor_interval` INT UNSIGNED NOT NULL DEFAULT 10,
  `query_execution_time` INT UNSIGNED NOT NULL DEFAULT 10,
  `query_data_retention` INT UNSIGNED NOT NULL DEFAULT 24,
  PRIMARY KEY (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `monitoring_servers` (
  `server_id` INT UNSIGNED NOT NULL,
  `available` TINYINT(1) NULL,
  `summary` TEXT NULL,
  `parameters` MEDIUMTEXT NULL,
  `processlist` MEDIUMTEXT NULL,
  `error` TEXT NULL,
  `updated` DATETIME NULL,
  PRIMARY KEY (`server_id`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `monitoring_queries` (
  `id` INT UNSIGNED AUTO_INCREMENT,
  `server_id` INT UNSIGNED NOT NULL,
  `query_id` INT UNSIGNED NOT NULL,
  `query_text` TEXT NOT NULL,
	`query_hash` VARCHAR(191) NOT NULL,
  `db` VARCHAR(191) NOT NULL,
  `user` VARCHAR(191) NOT NULL,
  `host` VARCHAR(191) NOT NULL,
  `first_seen` DATETIME NOT NULL,
  `last_seen` DATETIME NULL,
  `last_execution_time` INT UNSIGNED NULL,
  `max_execution_time` INT UNSIGNED NOT NULL,
  `bavg_execution_time` INT UNSIGNED NOT NULL,
  `avg_execution_time` INT UNSIGNED NOT NULL,
  `count` INT UNSIGNED NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE `server_id|db|query_hash` (`server_id`, `db`, `query_hash`),
  INDEX `server_id|last_execution_time` (`server_id`, `last_execution_time`),
  INDEX `server_id|max_execution_time` (`server_id`, `max_execution_time`),
  INDEX `server_id|avg_execution_time` (`server_id`, `avg_execution_time`),
  INDEX `server_id|count` (`server_id`, `count`),
  INDEX `query_text` (`query_text`(191)),
  INDEX `db` (`db`),
  INDEX `user` (`user`),
  INDEX `host` (`host`),
  INDEX `first_seen` (`first_seen`),
  INDEX `last_seen` (`last_seen`),
  INDEX `last_execution_time` (`last_execution_time`),
  INDEX `max_execution_time` (`max_execution_time`),
  INDEX `avg_execution_time` (`avg_execution_time`),
  INDEX `count` (`count`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `monitoring_events` (
  `id` INT UNSIGNED AUTO_INCREMENT,
  `server_id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(191) NOT NULL,
  `description` VARCHAR(191) NOT NULL,
  `status` TINYINT(1) NOT NULL,
  `data` TEXT NOT NULL,
  `created` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `server_id` (`server_id`),
  INDEX `name` (`name`),
  INDEX `description` (`description`),
  INDEX `created` (`created`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
);

CREATE TABLE `client_saved_queries` (
  `id` INT UNSIGNED AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `query` TEXT NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `name` (`name`),
  INDEX `user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);

CREATE TABLE `client_folders` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `user_id|name` (`user_id`, `name`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);

CREATE TABLE `client_servers` (
  `user_id` INT UNSIGNED NOT NULL,
  `server_id` INT UNSIGNED NOT NULL,
  `folder_id` INT UNSIGNED NULL,
  PRIMARY KEY (`user_id`, `server_id`),
  INDEX `server_id` (`server_id`),
  INDEX `folder_id` (`folder_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`),
  FOREIGN KEY (`folder_id`) REFERENCES `client_folders` (`id`)
);

CREATE TABLE `client_settings` (
  `user_id` INT UNSIGNED NOT NULL,
  `setting` VARCHAR(191) NOT NULL,
  `value` VARCHAR(191) NOT NULL,
  PRIMARY KEY (`user_id`, `setting`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);