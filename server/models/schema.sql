CREATE TABLE `settings` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
	`value` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

INSERT INTO settings (`name`, `value`) VALUES ('LOGS', '{"local": "","amazon_s3": {}}');

CREATE TABLE `users` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `coins` INT UNSIGNED NOT NULL DEFAULT '0',
  `group_id` int(10) unsigned NOT NULL,
  `admin` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `group_id` (`group_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `groups` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) NOT NULL,
  `description` text,
  `coins_day` INT UNSIGNED NOT NULL DEFAULT '25',
  `coins_max` INT UNSIGNED NOT NULL DEFAULT '100',
  `coins_execution` INT UNSIGNED NOT NULL DEFAULT '10',
  `deployments_enable` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_basic` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_pro` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_inbenta` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_edit` tinyint(1) NOT NULL DEFAULT '0',
  `deployments_execution_threads` tinyint(255) UNSIGNED NOT NULL DEFAULT '10',
  `deployments_execution_plan_factor` INT UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `environments` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`name`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `regions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `environment_id` int(10) unsigned NOT NULL,
  `cross_region` tinyint(1) NOT NULL,
  `hostname` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `key` text COLLATE utf8mb4_unicode_ci,
  `deploy_path` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `environment_id` (`environment_id`,`name`),
  CONSTRAINT `regions_ibfk_1` FOREIGN KEY (`environment_id`) REFERENCES `environments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `servers` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `engine` enum('MySQL','PostgreSQL') COLLATE utf8mb4_unicode_ci NOT NULL,
  `region_id` int(10) unsigned NOT NULL,
  `hostname` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `region_id` (`region_id`,`name`),
  FOREIGN KEY (`region_id`) REFERENCES `regions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `auxiliary` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int(10) unsigned NOT NULL,
  `hostname` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `username` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`name`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `slack` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `webhook` text COLLATE utf8mb4_unicode_ci,
  `enabled` tinyint(1) DEFAULT NULL,
  `group_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`),
  FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments` (
  `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(191) NOT NULL,
  `user_id` INT(10) UNSIGNED NOT NULL,
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_basic` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `deployment_id` INT UNSIGNED NOT NULL,
 `environment_id` INT(10) UNSIGNED NOT NULL,
 `databases` TEXT NOT NULL,
 `queries` TEXT NOT NULL,
 `method` ENUM('VALIDATE','TEST','DEPLOY') NOT NULL,
 `status` ENUM('CREATED','QUEUED','STARTING','IN PROGRESS','SUCCESS','WARNING','FAILED','STOPPING','STOPPED') NOT NULL DEFAULT 'CREATED',
 `created` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `progress` TEXT NULL,
 `error` TINYINT(1) NULL,
 `uri` VARCHAR(191) NULL,
 `engine` VARCHAR(191) NULL,
 `public` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `deployment_id` (`deployment_id`),
  KEY `uri` (`uri`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`),
  FOREIGN KEY (`environment_id`) REFERENCES `environments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_pro` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `deployment_id` INT UNSIGNED NOT NULL,
 `environment_id` INT(10) UNSIGNED NOT NULL,
 `code` MEDIUMTEXT NOT NULL,
 `method` ENUM('VALIDATE','TEST','DEPLOY') NOT NULL,
 `status` ENUM('CREATED','QUEUED','STARTING','IN PROGRESS','SUCCESS','WARNING','FAILED','STOPPING','STOPPED') NOT NULL DEFAULT 'CREATED',
 `created` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `progress` TEXT NULL,
 `error` TINYINT(1) NULL,
 `uri` VARCHAR(191) NULL,
 `engine` VARCHAR(191) NULL,
 `public` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY(id),
  KEY `deployment_id` (`deployment_id`),
  KEY `uri` (`uri`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`),
  FOREIGN KEY (`environment_id`) REFERENCES `environments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

CREATE TABLE `deployments_inbenta` (
 `id` INT UNSIGNED AUTO_INCREMENT,
 `deployment_id` INT UNSIGNED NOT NULL,
 `environment_id` INT(10) UNSIGNED NOT NULL,
 `products` SET('chatbot','km','no-product','search','ticketing') NOT NULL,
 `databases` TEXT NULL,
 `queries` TEXT NOT NULL,
 `status` ENUM('CREATED','QUEUED','STARTING','IN PROGRESS','SUCCESS','WARNING','FAILED','STOPPING','STOPPED') NOT NULL DEFAULT 'CREATED',
 `created` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 `started` DATETIME NULL,
 `ended` DATETIME NULL,
 `pid` INT UNSIGNED NULL,
 `progress` TEXT NULL,
 `error` TINYINT(1) NULL,
 `uri` VARCHAR(191) NULL,
 `engine` VARCHAR(191) NULL,
 `public` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `deployment_id` (`deployment_id`),
  KEY `uri` (`uri`),
  FOREIGN KEY (`deployment_id`) REFERENCES `deployments` (`id`),
  FOREIGN KEY (`environment_id`) REFERENCES `environments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;