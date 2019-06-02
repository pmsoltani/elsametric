-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema Scopus
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema Scopus
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `Scopus` DEFAULT CHARACTER SET utf8 ;
USE `Scopus` ;

-- -----------------------------------------------------
-- Table `Scopus`.`source`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`source` (
  `source_id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Auto Increment Source ID',
  `source_id_scp` BIGINT UNSIGNED NOT NULL COMMENT 'Unique Scopus Source (journal) ID',
  `title` VARCHAR(512) NOT NULL COMMENT 'Source Title',
  `url` VARCHAR(256) NOT NULL COMMENT 'Source url',
  `type` VARCHAR(45) NULL COMMENT 'Journal, Conference Proceeding, ...',
  `issn` INT(8) UNSIGNED NULL COMMENT 'Source Identifier',
  `e_issn` INT(8) UNSIGNED NULL,
  `isbn` INT(13) UNSIGNED NULL COMMENT 'Source Identifier',
  `publisher` VARCHAR(45) NULL COMMENT 'Source publisher',
  `country` VARCHAR(45) NULL,
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE INDEX `source_id_scp_UNIQUE` (`source_id_scp` ASC) VISIBLE,
  PRIMARY KEY (`source_id`),
  UNIQUE INDEX `source_id_UNIQUE` (`source_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`paper`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`paper` (
  `paper_id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Auto Increment Paper ID',
  `paper_id_scp` BIGINT UNSIGNED NOT NULL COMMENT 'Unique Scopus ID',
  `eid` VARCHAR(45) NOT NULL COMMENT 'Electronic ID',
  `title` VARCHAR(256) NOT NULL COMMENT '	\nArticle Title',
  `type` VARCHAR(10) NOT NULL COMMENT 'Document Type code',
  `type_description` VARCHAR(45) NULL COMMENT 'Document Type description',
  `abstract` TEXT NULL COMMENT 'Abstract',
  `total_author` SMALLINT UNSIGNED NOT NULL COMMENT 'Total number of authors',
  `open_access` TINYINT(1) UNSIGNED NOT NULL COMMENT 'True/False',
  `cited_cnt` SMALLINT UNSIGNED NOT NULL COMMENT 'Cited-by Count',
  `url` VARCHAR(256) NOT NULL COMMENT 'Scopus abstract detail page URL',
  `article_no` VARCHAR(45) NULL COMMENT '	\nArticle Number',
  `fund_no` VARCHAR(45) NULL COMMENT 'Funding Agency Identification',
  `retrieval_time` DATETIME NOT NULL COMMENT 'Date & time of accessing the paper info',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `source_id` INT UNSIGNED NOT NULL,
  `doi` VARCHAR(256) NULL COMMENT 'Document Object Identifier',
  `volume` VARCHAR(45) NULL COMMENT 'Volume',
  `issue` VARCHAR(45) NULL COMMENT 'Issue',
  `date` DATE NOT NULL COMMENT 'Publication Date',
  `page_range` VARCHAR(45) NULL COMMENT 'Page',
  UNIQUE INDEX `paper_id_scp_UNIQUE` (`paper_id_scp` ASC) VISIBLE,
  UNIQUE INDEX `eid_UNIQUE` (`eid` ASC) VISIBLE,
  UNIQUE INDEX `url_UNIQUE` (`url` ASC) VISIBLE,
  PRIMARY KEY (`paper_id`),
  UNIQUE INDEX `paper_id_UNIQUE` (`paper_id` ASC) VISIBLE,
  INDEX `fk_paper_source1_idx` (`source_id` ASC) VISIBLE,
  CONSTRAINT `fk_paper_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `Scopus`.`source` (`source_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = '		';


-- -----------------------------------------------------
-- Table `Scopus`.`author`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`author` (
  `author_id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Auto Increment Author ID',
  `author_id_scp` BIGINT UNSIGNED NOT NULL COMMENT 'Unique Scopus Author ID',
  `first` VARCHAR(45) NULL,
  `last` VARCHAR(45) NULL,
  `initials` VARCHAR(45) NULL,
  `sex` TINYINT(1) UNSIGNED NULL,
  `type` VARCHAR(45) NULL COMMENT 'Type of author (faculty, student, researcher)',
  `rank` VARCHAR(45) NULL COMMENT 'Rank of author (Full, Associate, Assitant Prof.; B.Sc., M.Sc., Ph.D. Student; Postdoc Researcher)',
  `email` VARCHAR(256) NULL COMMENT 'Email address of the author',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE INDEX `author_id_scp_UNIQUE` (`author_id_scp` ASC) VISIBLE,
  PRIMARY KEY (`author_id`),
  UNIQUE INDEX `author_id_UNIQUE` (`author_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`department`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`department` (
  `department_id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Auto Increment Department ID',
  `name` VARCHAR(128) NOT NULL COMMENT 'Department name',
  `abbreviation` VARCHAR(45) NULL COMMENT 'Department abbreviation',
  `type` VARCHAR(45) NULL COMMENT 'Department, Research Center, Research Institute, Center of Excellence, ...',
  `lat` DECIMAL(8,6) NULL COMMENT 'Department\'s main building\'s latitute',
  `lng` DECIMAL(9,6) NULL COMMENT 'Department\'s main building\'s longitude',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`department_id`),
  UNIQUE INDEX `department_id_UNIQUE` (`department_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`institution`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`institution` (
  `institution_id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Auto Increment Institution ID',
  `institution_id_scp` BIGINT UNSIGNED NOT NULL COMMENT 'Unique Scopus Affiliation (Institution) ID',
  `name` VARCHAR(128) NOT NULL COMMENT 'Institution name',
  `abbreviation` VARCHAR(45) NULL COMMENT 'Institution abbreviation',
  `city` VARCHAR(45) NULL COMMENT 'Institution city',
  `country` VARCHAR(45) NULL COMMENT 'Institution country',
  `url` VARCHAR(256) NULL COMMENT 'Scopus affiliation profile page',
  `type` VARCHAR(45) NULL COMMENT 'University, College, Business School, ...',
  `lat` DECIMAL(8,6) NULL COMMENT 'Institution\'s latitute',
  `lng` DECIMAL(9,6) NULL COMMENT 'Institution\'s longitude',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`institution_id`),
  UNIQUE INDEX `institution_id_scp_UNIQUE` (`institution_id_scp` ASC) VISIBLE,
  UNIQUE INDEX `institution_id_UNIQUE` (`institution_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`subject`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`subject` (
  `subject_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `asjc_code` INT UNSIGNED NOT NULL,
  `top` VARCHAR(128) NOT NULL,
  `middle` VARCHAR(128) NOT NULL,
  `low` VARCHAR(128) NOT NULL,
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`subject_id`),
  UNIQUE INDEX `subject_id_UNIQUE` (`subject_id` ASC) VISIBLE,
  UNIQUE INDEX `asjc_code_UNIQUE` (`asjc_code` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`source_subject`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`source_subject` (
  `source_id` INT UNSIGNED NOT NULL,
  `subject_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`source_id`, `subject_id`),
  INDEX `fk_source_has_subject_subject1_idx` (`subject_id` ASC) VISIBLE,
  INDEX `fk_source_has_subject_source1_idx` (`source_id` ASC) VISIBLE,
  CONSTRAINT `fk_source_has_subject_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `Scopus`.`source` (`source_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_source_has_subject_subject1`
    FOREIGN KEY (`subject_id`)
    REFERENCES `Scopus`.`subject` (`subject_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`paper_author`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`paper_author` (
  `paper_id` INT UNSIGNED NOT NULL,
  `author_id` INT UNSIGNED NOT NULL,
  `author_no` SMALLINT UNSIGNED NOT NULL COMMENT 'Position of author among other authors of the paper',
  PRIMARY KEY (`paper_id`, `author_id`),
  INDEX `fk_paper_has_author_author2_idx` (`author_id` ASC) VISIBLE,
  INDEX `fk_paper_has_author_paper1_idx` (`paper_id` ASC) VISIBLE,
  CONSTRAINT `fk_paper_has_author_paper1`
    FOREIGN KEY (`paper_id`)
    REFERENCES `Scopus`.`paper` (`paper_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_paper_has_author_author2`
    FOREIGN KEY (`author_id`)
    REFERENCES `Scopus`.`author` (`author_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`author_department`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`author_department` (
  `author_id` INT UNSIGNED NOT NULL,
  `department_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`author_id`, `department_id`),
  INDEX `fk_author_has_department_department2_idx` (`department_id` ASC) VISIBLE,
  INDEX `fk_author_has_department_author2_idx` (`author_id` ASC) VISIBLE,
  CONSTRAINT `fk_author_has_department_author2`
    FOREIGN KEY (`author_id`)
    REFERENCES `Scopus`.`author` (`author_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_author_has_department_department2`
    FOREIGN KEY (`department_id`)
    REFERENCES `Scopus`.`department` (`department_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`department_institution`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`department_institution` (
  `department_id` INT UNSIGNED NOT NULL,
  `institution_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`department_id`, `institution_id`),
  INDEX `fk_department_has_institution_institution2_idx` (`institution_id` ASC) VISIBLE,
  INDEX `fk_department_has_institution_department2_idx` (`department_id` ASC) VISIBLE,
  CONSTRAINT `fk_department_has_institution_department2`
    FOREIGN KEY (`department_id`)
    REFERENCES `Scopus`.`department` (`department_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_department_has_institution_institution2`
    FOREIGN KEY (`institution_id`)
    REFERENCES `Scopus`.`institution` (`institution_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`author_profile`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`author_profile` (
  `author_id` INT UNSIGNED NOT NULL,
  `url` VARCHAR(256) NOT NULL COMMENT 'Profile URL',
  `type` VARCHAR(45) NOT NULL COMMENT 'Scopus, Google Scholar, ResearchGate, Personal Webpage, ...',
  UNIQUE INDEX `url_UNIQUE` (`url` ASC) VISIBLE,
  PRIMARY KEY (`author_id`),
  CONSTRAINT `fk_author_profile_author1`
    FOREIGN KEY (`author_id`)
    REFERENCES `Scopus`.`author` (`author_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
