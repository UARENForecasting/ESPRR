-- migrate:up
drop procedure `create_system_data`;
create definer = 'insert_objects'@'localhost'
  procedure create_system_data (auth0id varchar(32), systemid char(36),
    dataset varchar(32))
    comment 'Create a system data row for processing'
    modifies sql data sql security definer
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
  end;
grant update(timeseries, statistics, error) on system_data to 'insert_objects'@'localhost';
grant execute on procedure `create_system_data` to 'insert_objects'@'localhost';
grant execute on procedure `create_system_data` to 'apiuser'@'%';


-- migrate:down
drop procedure `create_system_data`;
create definer = 'insert_objects'@'localhost'
  procedure create_system_data (auth0id varchar(32), systemid char(36),
    dataset varchar(32))
    comment 'Create a system data row for processing'
    modifies sql data sql security definer
  begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));

    if allowed then
      insert into system_data (system_id, dataset) values (binid, dataset);
    else
      signal sqlstate '42000' set message_text = 'Create system data denied',
        mysql_errno = 1142;
    end if;
  end;
revoke update(timeseries, statistics, error) on system_data from 'insert_objects'@'localhost';
grant execute on procedure `create_system_data` to 'insert_objects'@'localhost';
grant execute on procedure `create_system_data` to 'apiuser'@'%';
