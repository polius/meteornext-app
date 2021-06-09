CREATE TABLE `licenses` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `key` VARCHAR(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `expiration` DATETIME NOT NULL,
  `in_use` TINYINT(1) NOT NULL DEFAULT 0,
  `uuid` VARCHAR(191) NULL COLLATE utf8mb4_unicode_ci NULL,
  `last_used` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;