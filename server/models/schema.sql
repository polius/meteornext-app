CREATE TABLE `settings` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
	`value` TEXT NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

INSERT INTO settings (`id`, `name`, `value`) VALUES 
(1, 'FILES', '{"local":{"path":"","expire":"7"},"amazon_s3":{"enabled":false,"aws_access_key":"","aws_secret_access_key":"","region":"","bucket":""}}'),
(2, 'SECURITY', '{"password_age":"0","password_min":"8","password_lowercase":false,"password_uppercase":false,"password_number":false,"password_special":false,"force_mfa":false,"restrict_url":""}');

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
  `monitoring_interval` INT UNSIGNED NOT NULL DEFAULT 10,
  `utils_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `utils_import` tinyint(1) NOT NULL DEFAULT '0',
  `utils_export` tinyint(1) NOT NULL DEFAULT '0',
  `utils_import_limit` BIGINT UNSIGNED NULL,
  `utils_slack_enabled` TINYINT(1) NOT NULL DEFAULT '0',
  `utils_slack_name` VARCHAR(191) NULL,
  `utils_slack_url` VARCHAR(191) NULL,
  `client_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `client_limits` tinyint(1) NOT NULL DEFAULT '0',
  `client_limits_timeout_mode` INT UNSIGNED NOT NULL DEFAULT '1',
  `client_limits_timeout_value` INT UNSIGNED NOT NULL DEFAULT '10',
  `client_tracking` tinyint(1) NOT NULL DEFAULT '0',
  `client_tracking_retention` INT UNSIGNED NOT NULL DEFAULT '1',
  `client_tracking_mode` INT UNSIGNED NOT NULL DEFAULT '1',
  `client_tracking_filter` INT UNSIGNED NOT NULL DEFAULT '1',
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
  `disabled` TINYINT(1) NOT NULL DEFAULT '0',
  `change_password` TINYINT(1) NOT NULL DEFAULT '0',
  `last_login` DATETIME NULL,
  `last_ping` DATETIME NULL,
  `ip` VARCHAR(191) NULL,
  `user_agent` TEXT NULL,
  `created_by` INT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_by` INT UNSIGNED NULL,
  `updated_at` DATETIME NULL,
  `password_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `group_id` (`group_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `user_mfa` (
  `user_id` INT UNSIGNED NOT NULL,
  `2fa_hash` VARCHAR(191) NULL,
  `webauthn_pub_key` TEXT NULL,
  `webauthn_credential_id` TEXT NULL,
  `webauthn_sign_count` INT UNSIGNED NULL,
  `webauthn_rp_id` TEXT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
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

CREATE TABLE `regions_update` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `execution_id` INT UNSIGNED NOT NULL,
  `region_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `region_id` (`region_id`)
  /*
  INDEX `execution_id` (`execution_id`)
  FOREIGN KEY (`execution_id`) REFERENCES `executions` (`id`)
  FOREIGN KEY (`region_id`) REFERENCES `regions` (`id`)
  */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `servers` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int(10) unsigned NULL,
  `region_id` int(10) unsigned NULL,
  `engine` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hostname` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `port` INT UNSIGNED NOT NULL,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ssl` tinyint(1) NOT NULL DEFAULT '0',
  `ssl_client_key` text COLLATE utf8mb4_unicode_ci,
  `ssl_client_certificate` text COLLATE utf8mb4_unicode_ci,
  `ssl_ca_certificate` text COLLATE utf8mb4_unicode_ci,
  `ssl_verify_ca` tinyint(1) NOT NULL DEFAULT '0',
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
  `engine`  varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version`  varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hostname` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `port` INT UNSIGNED NOT NULL,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ssl` tinyint(1) NOT NULL,
  `ssl_client_key` text COLLATE utf8mb4_unicode_ci,
  `ssl_client_certificate` text COLLATE utf8mb4_unicode_ci,
  `ssl_ca_certificate` text COLLATE utf8mb4_unicode_ci,
  `ssl_verify_ca` tinyint(1) NOT NULL DEFAULT '0',
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

CREATE TABLE `cloud` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` INT UNSIGNED NOT NULL,
  `type` ENUM('aws','google') NOT NULL,
  `access_key` VARCHAR(191) NOT NULL,
  `secret_key` VARCHAR(191) NOT NULL,
  `buckets` TEXT NULL,
  `shared` TINYINT(1) NOT NULL,
  `owner_id` INT UNSIGNED NULL,
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
  `shared` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `name` (`name`),
  KEY `release_id` (`release_id`),
  KEY `user_id` (`user_id`),
  KEY `shared` (`shared`),
  FOREIGN KEY (`release_id`) REFERENCES `releases` (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `executions` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `deployment_id` INT UNSIGNED NOT NULL,
 `environment_id` INT(10) UNSIGNED NULL,
 `mode` ENUM('BASIC','PRO') NOT NULL,
 `databases` TEXT NULL,
 `queries` TEXT NULL,
 `code` MEDIUMTEXT NULL,
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
 `uri` VARCHAR(191) NOT NULL,
 `logs` VARCHAR(191) NULL,
 `expired` TINYINT(1) NOT NULL DEFAULT 0,
 `user_id` INT UNSIGNED NULL,
  PRIMARY KEY (`id`),
  UNIQUE `uri` (`uri`),
  KEY `deployment_id` (`deployment_id`),
  KEY `environment_id` (`environment_id`),
  KEY `mode` (`mode`),
  KEY `status` (`status`),
  KEY `created` (`created`),
  KEY `scheduled` (`scheduled`),
  KEY `started` (`started`),
  KEY `ended` (`ended`),
  KEY `expired` (`expired`),
  KEY `user_id` (`user_id`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`),
  FOREIGN KEY (`environment_id`) REFERENCES `environments` (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_queued` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT,
  `execution_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `execution_id` (`execution_id`),
  FOREIGN KEY (`execution_id`) REFERENCES `executions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_finished` (
  `execution_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`execution_id`),
  FOREIGN KEY (`execution_id`) REFERENCES `executions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_pinned` (
  `user_id` INT UNSIGNED NOT NULL,
  `deployment_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`user_id`,`deployment_id`),
  INDEX `deployment_id` (`deployment_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_shared` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED NOT NULL,
  `deployment_id` INT UNSIGNED NOT NULL,
  `is_pinned` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
  `created` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `user_id__deployment_id` (`user_id`,`deployment_id`),
  INDEX `deployment_id` (`deployment_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `notifications` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `status` ENUM('INFO','SUCCESS','WARNING','ERROR') NOT NULL,
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
  `date` DATETIME NOT NULL,
  PRIMARY KEY (`user_id`, `server_id`),
  INDEX (`server_id`),
  INDEX (`date`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `monitoring_settings` (
  `user_id` INT UNSIGNED NOT NULL,
  `monitor_align` TINYINT UNSIGNED NOT NULL DEFAULT 4,
  `monitor_slack_enabled` TINYINT(1) NOT NULL DEFAULT '0',
  `monitor_slack_url` VARCHAR(191) NULL,
  `monitor_base_url` VARCHAR(191) NOT NULL,
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
  INDEX `server_id` (`server_id`),
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
  `event` VARCHAR(191) NOT NULL,
  `data` TEXT NULL,
  `time` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `server_id` (`server_id`),
  INDEX `time` (`time`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `client_saved_queries` (
  `id` INT UNSIGNED AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `query` TEXT NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `name` (`name`),
  INDEX `user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `client_folders` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `user_id|name` (`user_id`, `name`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `client_servers` (
  `user_id` INT UNSIGNED NOT NULL,
  `server_id` INT UNSIGNED NOT NULL,
  `folder_id` INT UNSIGNED NULL,
  `date` DATETIME NOT NULL,
  PRIMARY KEY (`user_id`, `server_id`),
  INDEX `server_id` (`server_id`),
  INDEX `folder_id` (`folder_id`),
  INDEX `date` (`date`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`),
  FOREIGN KEY (`folder_id`) REFERENCES `client_folders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `client_settings` (
  `user_id` INT UNSIGNED NOT NULL,
  `setting` VARCHAR(191) NOT NULL,
  `value` VARCHAR(191) NOT NULL,
  PRIMARY KEY (`user_id`, `setting`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `client_queries` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `date` DATETIME NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  `server_id` INT UNSIGNED NOT NULL,
  `database` VARCHAR(191) NULL,
  `query` TEXT NOT NULL,
  `status` TINYINT(1) NOT NULL,
  `records` INT UNSIGNED NULL,
  `elapsed` VARCHAR(191) NULL,
  `error` TEXT NULL,
  PRIMARY KEY (`id`),
  INDEX `date` (`date`),
  INDEX `user_id` (`user_id`),
  INDEX `server_id` (`server_id`),
  INDEX `database` (`database`),
  INDEX `query` (`query`(191)),
  INDEX `status` (`status`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `imports` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `mode` ENUM('file','url','cloud') NOT NULL,
 `details` TEXT NULL,
 `source` TEXT NOT NULL,
 `selected` TEXT NULL,
 `size` BIGINT UNSIGNED NOT NULL,
 `server_id` INT UNSIGNED NOT NULL,
 `database` VARCHAR(191) NOT NULL,
 `create_database` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
 `drop_database` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
 `status` ENUM('CREATED','IN PROGRESS','SUCCESS','FAILED','STOPPED') NOT NULL,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `updated` DATETIME NULL,
 `uri` VARCHAR(191) NULL,
 `progress` TEXT NULL,
 `upload` TEXT NULL,
 `error` TEXT NULL,
 `stop` TINYINT(1) NOT NULL DEFAULT '0',
 `user_id` INT UNSIGNED NOT NULL,
 `deleted` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `mode` (`mode`),
  KEY `source` (`source`(191)),
  KEY `size` (`size`),
  KEY `server_id` (`server_id`),
  KEY `database` (`database`),
  KEY `status` (`status`),
  KEY `started` (`started`),
  KEY `ended` (`ended`),
  KEY `error` (`error`(1)),
  KEY `uri` (`uri`),
  KEY `user_id` (`user_id`),
  KEY `deleted` (`deleted`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `imports_scans` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `mode` ENUM('url','cloud') NOT NULL,
 `cloud_id` INT UNSIGNED NULL,
 `bucket` TEXT NULL,
 `source` TEXT NOT NULL,
 `size` BIGINT UNSIGNED NOT NULL,
 `status` ENUM('IN PROGRESS','SUCCESS','FAILED','STOPPED') NOT NULL,
 `updated` DATETIME NULL,
 `readed` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `uri` VARCHAR(191) NULL,
 `progress` TEXT NULL,
 `error` TEXT NULL,
 `data` TEXT NULL,
 `user_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  KEY `status` (`status`),
  KEY `updated` (`updated`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `exports` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `server_id` INT UNSIGNED NOT NULL,
 `database` VARCHAR(191) NOT NULL,
 `mode` ENUM('full','partial') NOT NULL,
 `format` ENUM('sql','csv') NOT NULL,
 `tables` TEXT NULL,
 `export_schema` TINYINT(1) UNSIGNED NOT NULL,
 `export_data` TINYINT(1) UNSIGNED NOT NULL,
 `add_drop_table` TINYINT(1) UNSIGNED NOT NULL,
 `export_triggers` TINYINT(1) UNSIGNED,
 `export_routines` TINYINT(1) UNSIGNED,
 `export_events` TINYINT(1) UNSIGNED,
 `size` BIGINT UNSIGNED NOT NULL,
 `status` ENUM('CREATED','IN PROGRESS','SUCCESS','FAILED','STOPPED') NOT NULL,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `updated` DATETIME NULL,
 `uri` VARCHAR(191) NULL,
 `progress` TEXT NULL,
 `error` TEXT NULL,
 `stop` TINYINT(1) NOT NULL DEFAULT '0',
 `url` TEXT NULL,
 `user_id` INT UNSIGNED NOT NULL,
 `deleted` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `server_id` (`server_id`),
  KEY `database` (`database`),
  KEY `mode` (`mode`),
  KEY `format` (`format`),
  KEY `tables` (`tables`(191)),
  KEY `export_schema` (`export_schema`),
  KEY `export_data` (`export_data`),
  KEY `add_drop_table` (`add_drop_table`),
  KEY `export_triggers` (`export_triggers`),
  KEY `export_routines` (`export_routines`),
  KEY `export_events` (`export_events`),
  KEY `size` (`size`),
  KEY `status` (`status`),
  KEY `started` (`started`),
  KEY `ended` (`ended`),
  KEY `error` (`error`(191)),
  KEY `uri` (`uri`),
  KEY `url` (`url`(191)),
  KEY `user_id` (`user_id`),
  KEY `deleted` (`deleted`),
  FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;