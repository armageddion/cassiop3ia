-- ---
-- Globals
-- ---

-- SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
-- SET FOREIGN_KEY_CHECKS=0;

-- ---
-- Table 'user'
-- 
-- ---

DROP TABLE IF EXISTS `user`;
		
CREATE TABLE `user` (
  `id` INTEGER UNIQUE AUTO_INCREMENT,
  `username` VARCHAR(128) NULL DEFAULT NULL,
  `email` VARCHAR(128) NULL DEFAULT NULL,
  `password_hash` VARCHAR(128) NULL DEFAULT NULL,
  `about_me` VARCHAR(256) NULL DEFAULT NULL,
  `state` INTEGER(1) NULL DEFAULT 0,
  `last_online` DATETIME NULL DEFAULT NULL,
  `environment_id` INTEGER NULL DEFAULT NULL,
  `type` INTEGER NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'device'
-- 
-- ---

DROP TABLE IF EXISTS `device`;
		
CREATE TABLE `device` (
  `id` INTEGER UNIQUE AUTO_INCREMENT,
  `name` VARCHAR(128) NULL DEFAULT NULL,
  `IP` VARCHAR(15) NULL DEFAULT '10.0.0.125',
  `MAC` VARCHAR(17) NULL DEFAULT '00:00:00:00:00:00',
  `state` INTEGER(1) NULL DEFAULT 0,
  `last_online` DATETIME NULL DEFAULT '1000-01-01 00:00:00',
  `environment_id` INTEGER NULL DEFAULT NULL,
  `device_type` INTEGER NULL DEFAULT NULL,
  `user_id` INTEGER NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'user_types'
-- 
-- ---

DROP TABLE IF EXISTS `user_types`;
		
CREATE TABLE `user_types` (
  `id` INTEGER UNIQUE AUTO_INCREMENT,
  `type` VARCHAR(64) NULL DEFAULT 'guest',
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'device_types'
-- 
-- ---

DROP TABLE IF EXISTS `device_types`;
		
CREATE TABLE `device_types` (
  `id` INTEGER UNIQUE AUTO_INCREMENT,
  `type` VARCHAR(64) NULL DEFAULT 'guest',
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'states'
-- 
-- ---

DROP TABLE IF EXISTS `states`;
		
CREATE TABLE `states` (
  `id` INTEGER UNIQUE AUTO_INCREMENT,
  `state` VARCHAR(8) NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'routines'
-- 
-- ---

DROP TABLE IF EXISTS `routines`;
		
CREATE TABLE `routines` (
  `id` INTEGER UNIQUE AUTO_INCREMENT,
  `name` VARCHAR(128) NULL DEFAULT NULL,
  `time` TIME NULL DEFAULT NULL,
  `enabled` TINYINT NULL DEFAULT NULL,
  `triggered` TINYINT NULL DEFAULT NULL,
  `environment_id` INTEGER NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
);


-- ---
-- Table 'environment'
-- 
-- ---

DROP TABLE IF EXISTS `environment`;
		
CREATE TABLE `environment` (
  `id` INTEGER UNIQUE AUTO_INCREMENT,
  `name` VARCHAR(64) NULL DEFAULT 'guest',
  `latitude` INTEGER NULL DEFAULT NULL,
  `longitude` INTEGER NULL DEFAULT NULL,
  `city` VARCHAR(64) NULL DEFAULT NULL,
  `state` VARCHAR(64) NULL DEFAULT NULL,
  `country` VARCHAR(64) NULL DEFAULT NULL,
  `IP` VARCHAR(15) NULL DEFAULT NULL,
  `low` INTEGER NULL DEFAULT NULL,
  `high` INTEGER NULL DEFAULT NULL,
  `description` VARCHAR(64) NULL DEFAULT NULL,
  `sunrise` DATETIME NULL DEFAULT NULL,
  `sunset` DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
);

-- ---
-- Foreign Keys 
-- ---

ALTER TABLE `user` ADD FOREIGN KEY (state) REFERENCES `states` (`id`);
ALTER TABLE `user` ADD FOREIGN KEY (type) REFERENCES `user_types` (`id`);
ALTER TABLE `user` ADD FOREIGN KEY (environment_id) REFERENCES `environment` (`id`);
ALTER TABLE `device` ADD FOREIGN KEY (state) REFERENCES `states` (`id`);
ALTER TABLE `device` ADD FOREIGN KEY (environment_id) REFERENCES `environment` (`id`);
ALTER TABLE `device` ADD FOREIGN KEY (device_type) REFERENCES `device_types` (`id`);
ALTER TABLE `device` ADD FOREIGN KEY (user_id) REFERENCES `user` (`id`);
ALTER TABLE `routines` ADD FOREIGN KEY (environment_id) REFERENCES `environment` (`id`);

-- ---
-- set dome initial values 
-- ---
INSERT INTO `alfr3d`.`states` (`id`, `state`) VALUES ('1', 'offline');
INSERT INTO `alfr3d`.`states` (`id`, `state`) VALUES ('2', 'online');

INSERT INTO `alfr3d`.`user_types` (`id`, `type`) VALUES ('1', 'technoking');
INSERT INTO `alfr3d`.`user_types` (`id`, `type`) VALUES ('2', 'resident');
INSERT INTO `alfr3d`.`user_types` (`id`, `type`) VALUES ('3', 'guest');

INSERT INTO `alfr3d`.`device_types` (`id`, `type`) VALUES ('1', 'alfr3d');
INSERT INTO `alfr3d`.`device_types` (`id`, `type`) VALUES ('2', 'HW');
INSERT INTO `alfr3d`.`device_types` (`id`, `type`) VALUES ('3', 'guest');

INSERT INTO `alfr3d`.`user` (`id`, `username`, `email`, `password_hash`, `about_me`, `last_online`, `state`, `type`, `environment_id`) VALUES ('1', 'athos', 'athos@littl31.com', '\'pbkdf2:sha256:260000$EVLamhqzR2ib572V$29ecaf8e9ef809496eebf2cc1dafc1c865e0efa0184a89dcca63492ced5290bf\'', '', '1000-01-01 00:00:00', 1, 1, 1);
INSERT INTO `alfr3d`.`user` (`id`, `username`, `email`, `password_hash`, `about_me`, `last_online`, `state`, `type`, `environment_id`) VALUES ('2', 'unknown', '', '', '', '1000-01-01 00:00:00', 1, 3, 1);
INSERT INTO `alfr3d`.`environment` (`name`) VALUES ('test');
