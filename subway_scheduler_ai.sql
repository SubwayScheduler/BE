-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema subway_scheduler
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema subway_scheduler
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `subway_scheduler` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `subway_scheduler` ;

-- -----------------------------------------------------
-- Table `subway_scheduler`.`administrator`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`administrator` (
  `ID` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `password` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`ID`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`line`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`line` (
  `ID` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `route_shape` ENUM('ROUND-TRIP', 'CIRCULAR') NOT NULL DEFAULT 'ROUND-TRIP',
  PRIMARY KEY (`ID`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`station`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`station` (
  `ID` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `line_ID` INT NOT NULL,
  PRIMARY KEY (`ID`),
  INDEX `fk_station_line1_idx` (`line_ID` ASC) VISIBLE,
  CONSTRAINT `fk_station_line1`
    FOREIGN KEY (`line_ID`)
    REFERENCES `subway_scheduler`.`line` (`ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`platform`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`platform` (
  `station_ID` INT NOT NULL,
  `bound_to` TINYINT(1) NOT NULL,
  PRIMARY KEY (`station_ID`, `bound_to`),
  INDEX `fk_platform_station1_idx` (`station_ID` ASC) VISIBLE,
  CONSTRAINT `fk_platform_station1`
    FOREIGN KEY (`station_ID`)
    REFERENCES `subway_scheduler`.`station` (`ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`congestion`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`congestion` (
  `platform_station_ID` INT NOT NULL,
  `platform_bound_to` TINYINT(1) NOT NULL,
  `time_slot` TIME NOT NULL,
  `congest_status` DOUBLE NULL DEFAULT NULL,
  PRIMARY KEY (`platform_station_ID`, `platform_bound_to`, `time_slot`),
  INDEX `fk_congestion_platform1_idx` (`platform_station_ID` ASC, `platform_bound_to` ASC) VISIBLE,
  CONSTRAINT `fk_congestion_platform1`
    FOREIGN KEY (`platform_station_ID` , `platform_bound_to`)
    REFERENCES `subway_scheduler`.`platform` (`station_ID` , `bound_to`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`eta`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`eta` (
  `station_ID` INT NOT NULL,
  `ET` TIME NOT NULL,
  PRIMARY KEY (`station_ID`),
  INDEX `fk_eta_station1_idx` (`station_ID` ASC) VISIBLE,
  CONSTRAINT `fk_eta_station1`
    FOREIGN KEY (`station_ID`)
    REFERENCES `subway_scheduler`.`station` (`ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`garage`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`garage` (
  `line_ID` INT NOT NULL,
  `station_ID` INT NOT NULL,
  PRIMARY KEY (`line_ID`),
  INDEX `fk_garage_line1_idx` (`line_ID` ASC) VISIBLE,
  INDEX `fk_garage_station1_idx` (`station_ID` ASC) VISIBLE,
  UNIQUE INDEX `station_ID_UNIQUE` (`station_ID` ASC) VISIBLE,
  CONSTRAINT `fk_garage_line1`
    FOREIGN KEY (`line_ID`)
    REFERENCES `subway_scheduler`.`line` (`ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_garage_station1`
    FOREIGN KEY (`station_ID`)
    REFERENCES `subway_scheduler`.`station` (`ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`motorman`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`motorman` (
  `ID` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`ID`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`train`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`train` (
  `ID` INT NOT NULL AUTO_INCREMENT,
  `capacity` INT NOT NULL,
  `Line_ID` INT NOT NULL,
  PRIMARY KEY (`ID`),
  INDEX `Line_ID` (`Line_ID` ASC) VISIBLE,
  CONSTRAINT `train_ibfk_1`
    FOREIGN KEY (`Line_ID`)
    REFERENCES `subway_scheduler`.`line` (`ID`),
  CONSTRAINT `chk_capacity_positive`
    CHECK (capacity > 0))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `subway_scheduler`.`train_motorman`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `subway_scheduler`.`train_motorman` (
  `Train_ID` INT NOT NULL,
  `Motorman_ID` INT NOT NULL,
  PRIMARY KEY (`Train_ID`, `Motorman_ID`),
  INDEX `Motorman_ID` (`Motorman_ID` ASC) VISIBLE,
  CONSTRAINT `train_motorman_ibfk_1`
    FOREIGN KEY (`Train_ID`)
    REFERENCES `subway_scheduler`.`train` (`ID`),
  CONSTRAINT `train_motorman_ibfk_2`
    FOREIGN KEY (`Motorman_ID`)
    REFERENCES `subway_scheduler`.`motorman` (`ID`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
