/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`command_database` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `command_database`;

/*Table structure for table `command_table` */

DROP TABLE IF EXISTS `command_table`;

CREATE TABLE `command_table` (
  `Command_ID` varchar(16) PRIMARY KEY,
  `Command` varchar(300),
  `Command_Execution_Status` char(3),
  `Execution_Time` varchar(40),
  `Timestamp` datetime) ENGINE=InnoDB DEFAULT CHARSET=latin1;


