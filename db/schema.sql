/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `schema_migrations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schema_migrations` (
  `version` varchar(255) COLLATE latin1_bin NOT NULL,
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `system_data`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_data` (
  `system_id` binary(16) NOT NULL,
  `dataset` varchar(32) NOT NULL,
  `version` varchar(32) DEFAULT NULL,
  `system_hash` binary(16) DEFAULT NULL,
  `timeseries` longblob,
  `statistics` longblob,
  `error` json NOT NULL DEFAULT (json_array()),
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`system_id`,`dataset`),
  KEY `timeseries_null` (`timeseries`(1)),
  KEY `statistics_null` (`statistics`(1)),
  CONSTRAINT `system_data_ibfk_1` FOREIGN KEY (`system_id`) REFERENCES `systems` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=COMPRESSED;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `system_group_mapping`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_group_mapping` (
  `group_id` binary(16) NOT NULL,
  `system_id` binary(16) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`group_id`,`system_id`),
  KEY `systems` (`system_id`),
  CONSTRAINT `system_group_mapping_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `system_groups` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `system_group_mapping_ibfk_2` FOREIGN KEY (`system_id`) REFERENCES `systems` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=COMPRESSED;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `system_groups`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_groups` (
  `id` binary(16) NOT NULL DEFAULT (uuid_to_bin(uuid(),1)),
  `user_id` binary(16) NOT NULL,
  `name` varchar(128) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `system_user_name_key` (`user_id`,`name`),
  KEY `systems_user_id_key` (`user_id`),
  CONSTRAINT `system_groups_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=COMPRESSED;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `systems`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `systems` (
  `id` binary(16) NOT NULL DEFAULT (uuid_to_bin(uuid(),1)),
  `user_id` binary(16) NOT NULL,
  `name` varchar(128) NOT NULL,
  `definition` json NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `system_user_name_key` (`user_id`,`name`),
  KEY `systems_user_id_key` (`user_id`),
  CONSTRAINT `systems_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=COMPRESSED;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` binary(16) NOT NULL DEFAULT (uuid_to_bin(uuid(),1)),
  `auth0_id` varchar(32) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth0_id_key` (`auth0_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=COMPRESSED;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'esprr_data'
--
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` FUNCTION `check_users_system`(auth0id varchar(32), systemid char(36)) RETURNS tinyint(1)
    READS SQL DATA
    COMMENT 'Check if the system exists and belongs to user'
begin
    return exists(select 1 from systems where id = uuid_to_bin(systemid, 1)
                                          and user_id = get_user_binid(auth0id));
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` FUNCTION `check_users_system_group`(auth0id varchar(32), groupid char(36)) RETURNS tinyint(1)
    READS SQL DATA
    COMMENT 'Check if the system exists and belongs to user'
begin
    return exists(select 1 from system_groups where id = uuid_to_bin(groupid, 1)
                                              and user_id = get_user_binid(auth0id));
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` FUNCTION `does_user_exist`(auth0id varchar(32)) RETURNS tinyint(1)
    READS SQL DATA
    COMMENT 'Check if a user exists or not'
begin
    return exists(select 1 from users where auth0_id = auth0id);
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` FUNCTION `get_system_data_status`(binid binary(16), datasetin varchar(32)) RETURNS varchar(32) CHARSET utf8mb4
    READS SQL DATA
begin
    declare error_status boolean default (exists(
      select 1 from system_data where system_id = binid and dataset = datasetin
      and json_length(error) != 0));
    declare timeseries_status boolean default (exists(
      select 1 from system_data where system_id = binid and dataset = datasetin
      and timeseries is not null));
    declare stats_status boolean default (exists(
      select 1 from system_data where system_id = binid and dataset = datasetin
      and statistics is not null));

    if error_status then
      return 'error';
    elseif timeseries_status and stats_status then
      return 'complete';
    elseif timeseries_status and not stats_status then
      return 'statistics missing';
    elseif not timeseries_status and stats_status then
      return 'timeseries missing';
    else
      return 'prepared';
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` FUNCTION `get_user_binid`(auth0id varchar(32)) RETURNS binary(16)
    READS SQL DATA
    COMMENT 'Get the binary id of a user'
begin
    return (select id from users where auth0_id = auth0id);
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` FUNCTION `get_user_id`(auth0id varchar(32)) RETURNS char(36) CHARSET utf8mb4
    READS SQL DATA
    COMMENT 'Get the id of a user'
begin
    return (select bin_to_uuid(id, 1) from users where auth0_id = auth0id);
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `add_example_data`()
begin
  call _add_example_data_0();
  call _add_example_data_1();
  call _add_example_data_2();
end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`insert_objects`@`localhost` PROCEDURE `add_system_to_group`(auth0id varchar(32), systemid char(36), groupid char(128))
    MODIFIES SQL DATA
    COMMENT 'Add a system to a group'
begin
    declare bin_system_id binary(16) default (uuid_to_bin(systemid, 1));
    declare bin_group_id binary(16) default (uuid_to_bin(groupid, 1));

    declare allowed boolean default (
        check_users_system(auth0id, systemid)
        AND check_users_system_group(auth0id, groupid)
    );
    if allowed then
      insert into system_group_mapping (system_id, group_id) VALUES (bin_system_id, bin_group_id);
    else
      signal sqlstate '42000' set message_text = 'Adding system to group not allowed',
      mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`insert_objects`@`localhost` PROCEDURE `create_system`(auth0id varchar(32), name varchar(128), system_def JSON)
    MODIFIES SQL DATA
    COMMENT 'Create a new system'
begin
    declare sysid char(36) default (uuid());
    declare binid binary(16) default (uuid_to_bin(sysid, 1));
    insert into systems (id, user_id, name, definition) values (
      binid, get_user_binid(auth0id), name, system_def);
    select sysid as system_id;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`insert_objects`@`localhost` PROCEDURE `create_system_data`(auth0id varchar(32), systemid char(36),
    dataset varchar(32))
    MODIFIES SQL DATA
    COMMENT 'Create a system data row for processing'
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));

    if allowed then
      insert into system_data (system_id, dataset) values (binid, dataset)
      on duplicate key update timeseries = null, statistics = null, error = json_array();
    else
      signal sqlstate '42000' set message_text = 'Create system data denied',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`insert_objects`@`localhost` PROCEDURE `create_system_group`(auth0id varchar(32), name varchar(128))
    MODIFIES SQL DATA
    COMMENT 'Create a new system group'
begin
    declare groupid char(36) default (uuid());
    declare binid binary(16) default (uuid_to_bin(groupid, 1));
    insert into system_groups (id, user_id, name) values (
      binid, get_user_binid(auth0id), name);
    select groupid as group_id;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`insert_objects`@`localhost` PROCEDURE `create_user_if_not_exists`(in auth0id varchar(32))
    MODIFIES SQL DATA
    COMMENT 'Creates a user if nonexistent and returns the user id'
begin
    declare userid binary(16);
    if not does_user_exist(auth0id) then
      set userid = uuid_to_bin(uuid(), 1);
      insert into users (id, auth0_id) values (userid, auth0id);
      select bin_to_uuid(userid, 1) as user_id;
    else
      select get_user_id(auth0id) as user_id;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`delete_objects`@`localhost` PROCEDURE `delete_system`(auth0id varchar(32), systemid char(36))
    MODIFIES SQL DATA
    COMMENT 'Delete a system'
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));
    declare uid binary(16) default get_user_binid(auth0id);

    if allowed then
      delete from systems where id = binid;
    else
      signal sqlstate '42000' set message_text = 'Deleting system not allowed',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`delete_objects`@`localhost` PROCEDURE `delete_system_group`(auth0id varchar(32), groupid char(36))
    MODIFIES SQL DATA
    COMMENT 'Delete a system group'
begin
    declare binid binary(16) default (uuid_to_bin(groupid, 1));
    declare allowed boolean default (check_users_system_group(auth0id, groupid));
    declare uid binary(16) default get_user_binid(auth0id);

    if allowed then
      delete from system_groups where id = binid;
    else
      signal sqlstate '42000' set message_text = 'Deleting system group not allowed',
      mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`delete_objects`@`localhost` PROCEDURE `delete_user_by_auth0id`(in auth0id varchar(32))
    MODIFIES SQL DATA
    COMMENT 'Delete a user by auth0 ID'
begin
    declare userid binary(16);
    if does_user_exist(auth0id) then
      delete from users where auth0_id = auth0id;
    else
      signal sqlstate '42000' set message_text = 'User does not exist',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `get_group_systems`(auth0id varchar(32), groupid varchar(36))
    READS SQL DATA
    COMMENT 'Get name and id of each system that belongs to a group'
begin
    declare allowed boolean default(check_users_system_group(auth0id, groupid));
    if allowed then
        select bin_to_uuid(systems.id, 1) as system_id,
               bin_to_uuid(systems.user_id, 1) as user_id,
               name,
               definition,
               created_at,
               modified_at
        from systems WHERE id in (
            select system_id
            from system_group_mapping
            where group_id = uuid_to_bin(groupid, 1)
        );
    else
        signal sqlstate '42000' set message_text = 'System group inaccessible',
          mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `get_system`(auth0id varchar(32), systemid char(36))
    READS SQL DATA
    COMMENT 'Get the definition for a system'
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));

    if allowed then
      select bin_to_uuid(id, 1) as system_id, bin_to_uuid(user_id, 1) as user_id,
      name, definition, created_at, modified_at from systems where id = binid;
    else
      signal sqlstate '42000' set message_text = 'System inaccessible',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `get_system_data_meta`(auth0id varchar(32), systemid char(36),
    datasetid varchar(32))
    READS SQL DATA
    COMMENT 'Get the system data metadata'
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));
    declare row_present boolean default (exists(
      select 1 from system_data where system_id = binid and dataset = datasetid));


    if allowed and row_present then
      select bin_to_uuid(system_id, 1) as system_id,
        dataset, version, hex(system_hash) as system_hash,
        get_system_data_status(binid, datasetid) as status,
	error, created_at, modified_at
      from system_data where system_id = binid and dataset = datasetid;
    else
      signal sqlstate '42000' set message_text = 'Getting system data metadata denied',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `get_system_group`(auth0id varchar(32), groupid char(36))
    READS SQL DATA
    COMMENT 'Get the definition for a system group'
begin
    declare binid binary(16) default (uuid_to_bin(groupid, 1));
    declare allowed boolean default (check_users_system_group(auth0id, groupid));

    if allowed then
      select bin_to_uuid(id, 1) as group_id, bin_to_uuid(user_id, 1) as user_id,
      name, created_at, modified_at from system_groups where id = binid;
    else
      signal sqlstate '42000' set message_text = 'System inaccessible',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `get_system_hash`(auth0id varchar(32), systemid char(36))
    READS SQL DATA
begin
  declare binid binary(16) default (uuid_to_bin(systemid, 1));
  declare allowed boolean default (check_users_system(auth0id, systemid));

  if allowed then
    select md5(definition) as system_hash from systems where id = binid;
  else
    signal sqlstate '42000' set message_text = 'Getting system hash denied',
      mysql_errno = 1142;
  end if;
end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `get_system_statistics`(auth0id varchar(32), systemid char(36),
    datasetid varchar(32))
    READS SQL DATA
    COMMENT 'Get the statistics data for a system + dataset'
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));

    if allowed then
      select bin_to_uuid(system_id, 1) as system_id,
        dataset, version, system_hash, statistics, created_at, modified_at
	from system_data where system_id = binid and dataset = datasetid;
    else
      signal sqlstate '42000' set message_text = 'System statistics inaccessible',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `get_system_timeseries`(auth0id varchar(32), systemid char(36),
    datasetid varchar(32))
    READS SQL DATA
    COMMENT 'Get the timeseries data for a system + dataset'
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));

    if allowed then
      select bin_to_uuid(system_id, 1) as system_id,
        dataset, version, system_hash, timeseries, created_at, modified_at
	from system_data where system_id = binid and dataset = datasetid;
    else
      signal sqlstate '42000' set message_text = 'System timeseries inaccessible',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `get_user`(in auth0id varchar(32))
    READS SQL DATA
    COMMENT 'Get a user by auth0 id'
begin
    if does_user_exist(auth0id) then
      select bin_to_uuid(id, 1) as user_id, auth0_id, created_at from users where auth0_id = auth0id;
    else
      signal sqlstate '42000' set message_text = 'User does not exist',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `list_systems`(auth0id varchar(32))
    READS SQL DATA
    COMMENT 'List all user systems'
begin
    select bin_to_uuid(id, 1) as system_id, bin_to_uuid(user_id, 1) as user_id,
           name, definition, created_at, modified_at from systems
     where user_id = get_user_binid(auth0id);
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `list_system_data_status`()
    READS SQL DATA
begin
    select bin_to_uuid(system_id, 1) as system_id, dataset,
      get_system_data_status(system_id, dataset) as status, version,
      (system_hash != unhex(md5(systems.definition))) as hash_changed,
      users.auth0_id as user
    from system_data join (systems, users) on systems.id = system_data.system_id
    and systems.user_id = users.id;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`select_objects`@`localhost` PROCEDURE `list_system_groups`(auth0id varchar(32))
    READS SQL DATA
    COMMENT 'List all user system groups'
begin
    select bin_to_uuid(id, 1) as group_id, bin_to_uuid(user_id, 1) as user_id,
           name, created_at, modified_at from system_groups
     where user_id = get_user_binid(auth0id);
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `remove_example_data`()
    MODIFIES SQL DATA
begin
  call _remove_example_data_0;
end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`delete_objects`@`localhost` PROCEDURE `remove_system_from_group`(auth0id varchar(32), systemid char(36), groupid char(128))
    MODIFIES SQL DATA
    COMMENT 'Add a system to a group'
begin
    declare bin_system_id binary(16) default (uuid_to_bin(systemid, 1));
    declare bin_group_id binary(16) default (uuid_to_bin(groupid, 1));

    declare allowed boolean default (
        check_users_system(auth0id, systemid)
        AND check_users_system_group(auth0id, groupid)
    );
    if allowed then
      delete from system_group_mapping where system_id = bin_system_id and group_id = bin_group_id;
    else
      signal sqlstate '42000' set message_text = 'Adding system to group not allowed',
      mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`update_objects`@`localhost` PROCEDURE `report_failure`(systemid char(36), datasetname varchar(32), newerror JSON)
    MODIFIES SQL DATA
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));

    update system_data set error = newerror where system_id = binid and dataset = datasetname;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`update_objects`@`localhost` PROCEDURE `update_system`(auth0id varchar(32), systemid char(36), new_name varchar(128), system_def JSON)
    MODIFIES SQL DATA
    COMMENT 'Update a system definition'
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));
    declare uid binary(16) default get_user_binid(auth0id);

    if allowed then
      update systems set name = new_name, definition = system_def where id = binid;
    else
      signal sqlstate '42000' set message_text = 'Updating system not allowed',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`update_objects`@`localhost` PROCEDURE `update_system_data`(auth0id varchar(32), systemid char(36),
    datasetid varchar(32), new_timeseries longblob, new_statistics longblob,
    new_error JSON, new_version varchar(32), new_system_hash char(32))
    MODIFIES SQL DATA
    COMMENT 'Update the timeseries and stats data'
begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean;
    set allowed = check_users_system(auth0id, systemid) and exists(
      select 1 from system_data where system_id = binid and dataset = datasetid
      );

    if allowed then
      update system_data set version = new_version,
        system_hash = unhex(new_system_hash),
        timeseries = new_timeseries, statistics = new_statistics, error = new_error
	where system_id = binid and dataset = datasetid;
    else
      signal sqlstate '42000' set message_text = 'Updating system data denied',
        mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`update_objects`@`localhost` PROCEDURE `update_system_group`(auth0id varchar(32), groupid char(36), new_name varchar(128))
    MODIFIES SQL DATA
    COMMENT 'Update system group'
begin

    declare allowed boolean default(check_users_system_group(auth0id, groupid));
    declare binid binary(16) default (uuid_to_bin(groupid, 1));
    if allowed then
        update system_groups set name = new_name where id = binid;
    else
        signal sqlstate '42000' set message_text = 'Updating system group not allowed',
          mysql_errno = 1142;
    end if;
  end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `_add_example_data_0`()
    MODIFIES SQL DATA
begin
  set @userid = uuid_to_bin('17fbf1c6-34bd-11eb-af43-f4939feddd82', 1);
  set @otheruser = uuid_to_bin('972084d4-34cd-11eb-8f13-f4939feddd82', 1);
  set @sysid = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1);
  set @othersysid = uuid_to_bin('6513485a-34cd-11eb-8f13-f4939feddd82', 1);
  set @extime = timestamp('2020-12-01 01:23');
  set @sysdef = '{
       "name": "Test PV System",
       "boundary": {
           "nw_corner": {"latitude": 32.05, "longitude": -110.95},
           "se_corner": {"latitude": 32.01, "longitude": -110.85}
       },
       "ac_capacity": 10.0,
       "dc_ac_ratio": 1.2,
       "albedo": 0.2,
       "tracking": {
         "tilt": 20.0,
         "azimuth": 180.0
       }
     }';

  insert into users (auth0_id, id, created_at) values (
    'auth0|6061d0dfc96e2800685cb001', @userid, @extime
  ),(
    'auth0|invalid', @otheruser, @extime
    );
  insert into systems (id, user_id, name, definition, created_at, modified_at) values (
    @sysid, @userid, 'Test PV System', @sysdef, @extime, @extime
  ),(
    @othersysid, @otheruser, 'Other system', '{}', @extime, @extime
    );
end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `_add_example_data_1`()
    MODIFIES SQL DATA
begin
  set @sysid = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1);
  set @extime = timestamp('2020-12-01 01:23');
  set @syshash = (select unhex(md5(definition)) from systems where id = @sysid);
  insert into system_data (system_id, dataset, version, system_hash, timeseries, statistics, created_at, modified_at) values (
    @sysid, 'NSRDB_2019', 'v0.1', unhex('29b4855d70dc37601bb31323f9703cf1'),
    from_base64('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'),
    from_base64('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'),

    @extime, @extime
    );
end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `_add_example_data_2`()
    MODIFIES SQL DATA
begin
  set @sysid = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1);
  set @groupid = uuid_to_bin('3e622aaa-a187-11ec-ad64-54bf64606445', 1);
  set @userid = uuid_to_bin('17fbf1c6-34bd-11eb-af43-f4939feddd82', 1);
  insert into system_groups (
    id, name, user_id
  ) VALUES (
    @groupid, "A System Group", @userid
  );
  insert into system_group_mapping (
    group_id, system_id
  ) VALUES (
    @groupid, @sysid
  );
end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `_remove_example_data_0`()
    MODIFIES SQL DATA
begin
  set @userid = uuid_to_bin('17fbf1c6-34bd-11eb-af43-f4939feddd82', 1);
  set @sysid = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1);
  set @othersysid = uuid_to_bin('6513485a-34cd-11eb-8f13-f4939feddd82', 1);
  set @otheruser = uuid_to_bin('972084d4-34cd-11eb-8f13-f4939feddd82', 1);

  delete from systems where id = @sysid;
  delete from systems where id = @othersysid;
  delete from users where id = @userid;
  delete from users where id = @otheruser;
end ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed

--
-- Dbmate schema migrations
--

LOCK TABLES `schema_migrations` WRITE;
INSERT INTO `schema_migrations` (version) VALUES
  ('20210329141817'),
  ('20210329142022'),
  ('20210329142645'),
  ('20210329144831'),
  ('20210412153722'),
  ('20210419193357'),
  ('20210429174612'),
  ('20220302095800');
UNLOCK TABLES;
