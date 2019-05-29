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
  `source_id` INT NOT NULL COMMENT 'Unique Scopus Source (journal) ID',
  `title` VARCHAR(128) NOT NULL COMMENT 'Source Title',
  `url` VARCHAR(256) NOT NULL COMMENT 'Source url',
  `issn` INT(8) NULL COMMENT 'Source Identifier',
  `isbn` INT(13) NULL COMMENT 'Source Identifier',
  `subject` TEXT NULL COMMENT 'Source subject(s)',
  `publisher` VARCHAR(45) NULL COMMENT 'Source publisher',
  `type` VARCHAR(45) NULL COMMENT 'Journal, Conference Proceeding, ...',
  PRIMARY KEY (`source_id`),
  UNIQUE INDEX `source_id_UNIQUE` (`source_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`paper`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`paper` (
  `paper_id` INT NOT NULL COMMENT 'Unique Scopus ID',
  `eid` VARCHAR(45) NOT NULL COMMENT 'Electronic ID',
  `title` VARCHAR(256) NOT NULL COMMENT '	\nArticle Title',
  `type` VARCHAR(10) NOT NULL COMMENT 'Document Type code',
  `type_description` VARCHAR(45) NULL COMMENT 'Document Type description',
  `abstract` TEXT NULL COMMENT 'Abstract',
  `total_author` SMALLINT NOT NULL COMMENT 'Total number of authors',
  `open_access` TINYINT(1) NOT NULL COMMENT 'True/False',
  `cited_cnt` SMALLINT NOT NULL COMMENT 'Cited-by Count',
  `url` VARCHAR(256) NOT NULL COMMENT 'Scopus abstract detail page URL',
  `article_no` VARCHAR(45) NULL COMMENT '	\nArticle Number',
  `fund_no` VARCHAR(45) NULL COMMENT 'Funding Agency Identification',
  `retrieval_time` DATETIME NOT NULL COMMENT 'Date & time of accessing the paper info',
  `create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
  `source_id` INT NOT NULL COMMENT 'Unique Scopus Source (journal) ID',
  `doi` VARCHAR(256) NULL COMMENT 'Document Object Identifier',
  `volume` VARCHAR(45) NULL COMMENT 'Volume',
  `issue` VARCHAR(45) NULL COMMENT 'Issue',
  `date` DATE NOT NULL COMMENT 'Publication Date',
  `page_range` VARCHAR(45) NULL COMMENT 'Page',
  PRIMARY KEY (`paper_id`, `source_id`),
  UNIQUE INDEX `paper_id_UNIQUE` (`paper_id` ASC) VISIBLE,
  UNIQUE INDEX `eid_UNIQUE` (`eid` ASC) VISIBLE,
  UNIQUE INDEX `url_UNIQUE` (`url` ASC) VISIBLE,
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
  `author_id` INT NOT NULL COMMENT 'Unique Scopus Author ID',
  `first` VARCHAR(45) NULL,
  `last` VARCHAR(45) NULL,
  `initials` VARCHAR(45) NULL,
  `sex` TINYINT(1) NULL,
  `type` VARCHAR(45) NULL COMMENT 'Type of author (faculty, student, researcher)',
  `rank` VARCHAR(45) NULL COMMENT 'Rank of author (Full, Associate, Assitant Prof.; B.Sc., M.Sc., Ph.D. Student; Postdoc Researcher)',
  `email` VARCHAR(128) NULL COMMENT 'Email address of the author',
  PRIMARY KEY (`author_id`),
  UNIQUE INDEX `author_id_UNIQUE` (`author_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`department`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`department` (
  `department_id` INT NOT NULL AUTO_INCREMENT COMMENT 'Generated department ID',
  `name` VARCHAR(128) NOT NULL COMMENT 'Department name',
  `abbreviation` VARCHAR(45) NULL COMMENT 'Department abbreviation',
  `type` VARCHAR(45) NULL COMMENT 'Department, Research Center, Research Institute, Center of Excellence, ...',
  `lat` DECIMAL(8,6) NULL COMMENT 'Department\'s main building\'s latitute',
  `lng` DECIMAL(9,6) NULL COMMENT 'Department\'s main building\'s longitude',
  PRIMARY KEY (`department_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`institution`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`institution` (
  `institution_id` INT NOT NULL COMMENT 'Unique Scopus Affiliation (Institution) ID',
  `name` VARCHAR(128) NOT NULL COMMENT 'Institution name',
  `abbreviation` VARCHAR(45) NULL COMMENT 'Institution abbreviation',
  `city` VARCHAR(45) NULL COMMENT 'Institution city',
  `country` VARCHAR(45) NULL COMMENT 'Institution country',
  `url` VARCHAR(256) NULL COMMENT 'Scopus affiliation profile page',
  `type` VARCHAR(45) NULL COMMENT 'University, College, Business School, ...',
  `lat` DECIMAL(8,6) NULL COMMENT 'Institution\'s latitute',
  `lng` DECIMAL(9,6) NULL COMMENT 'Institution\'s longitude',
  PRIMARY KEY (`institution_id`),
  UNIQUE INDEX `institution_id_UNIQUE` (`institution_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`paper_author`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`paper_author` (
  `paper_id` INT NOT NULL,
  `author_id` INT NOT NULL,
  `author_cnt` SMALLINT NOT NULL COMMENT 'Position of author among other authors of the paper',
  PRIMARY KEY (`paper_id`, `author_id`),
  INDEX `fk_paper_has_author_author1_idx` (`author_id` ASC) VISIBLE,
  INDEX `fk_paper_has_author_paper_idx` (`paper_id` ASC) VISIBLE,
  CONSTRAINT `fk_paper_has_author_paper`
    FOREIGN KEY (`paper_id`)
    REFERENCES `Scopus`.`paper` (`paper_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_paper_has_author_author1`
    FOREIGN KEY (`author_id`)
    REFERENCES `Scopus`.`author` (`author_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`author_department`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`author_department` (
  `author_id` INT NOT NULL,
  `department_id` INT NOT NULL,
  PRIMARY KEY (`author_id`, `department_id`),
  INDEX `fk_author_has_department_department1_idx` (`department_id` ASC) VISIBLE,
  INDEX `fk_author_has_department_author1_idx` (`author_id` ASC) VISIBLE,
  CONSTRAINT `fk_author_has_department_author1`
    FOREIGN KEY (`author_id`)
    REFERENCES `Scopus`.`author` (`author_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_author_has_department_department1`
    FOREIGN KEY (`department_id`)
    REFERENCES `Scopus`.`department` (`department_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Scopus`.`department_institution`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Scopus`.`department_institution` (
  `department_id` INT NOT NULL,
  `institution_id` INT NOT NULL,
  PRIMARY KEY (`department_id`, `institution_id`),
  INDEX `fk_department_has_institution_institution1_idx` (`institution_id` ASC) VISIBLE,
  INDEX `fk_department_has_institution_department1_idx` (`department_id` ASC) VISIBLE,
  CONSTRAINT `fk_department_has_institution_department1`
    FOREIGN KEY (`department_id`)
    REFERENCES `Scopus`.`department` (`department_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_department_has_institution_institution1`
    FOREIGN KEY (`institution_id`)
    REFERENCES `Scopus`.`institution` (`institution_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
