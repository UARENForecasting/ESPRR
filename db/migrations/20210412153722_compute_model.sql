-- migrate:up
create table system_data(
  system_id binary(16) not null,
  dataset varchar(32) not null,
  version varchar(32),
  system_hash binary(16),
  timeseries longblob,
  statistics longblob,
  created_at timestamp not null default current_timestamp,
  modified_at timestamp not null default current_timestamp on update current_timestamp,
  primary key system_dataset_key (system_id, dataset),
  key timeseries_null (timeseries(1)),
  key statistics_null (statistics(1)),
  foreign key (system_id)
    references systems(id)
    on delete cascade on update restrict
) engine=innodb row_format=compressed;


-- get timeseries
create definer = 'select_objects'@'localhost'
  procedure get_system_timeseries (auth0id varchar(32), systemid char(36),
    datasetid varchar(32))
    comment 'Get the timeseries data for a system + dataset'
    reads sql data sql security definer
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
  end;
  
grant select on system_data to 'select_objects'@'localhost';
grant execute on procedure `get_system_timeseries` to 'select_objects'@'localhost';
grant execute on procedure `get_system_timeseries` to 'apiuser'@'%';


-- get stats
create definer = 'select_objects'@'localhost'
  procedure get_system_statistics (auth0id varchar(32), systemid char(36),
    datasetid varchar(32))
    comment 'Get the statistics data for a system + dataset'
    reads sql data sql security definer
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
  end;
  
grant execute on procedure `get_system_statistics` to 'select_objects'@'localhost';
grant execute on procedure `get_system_statistics` to 'apiuser'@'%';


-- create data obj
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

grant insert on system_data to 'insert_objects'@'localhost';
grant execute on function `check_users_system` to 'insert_objects'@'localhost';
grant execute on procedure `create_system_data` to 'insert_objects'@'localhost';
grant execute on procedure `create_system_data` to 'apiuser'@'%';


-- update data
create definer = 'update_objects'@'localhost'
  procedure update_system_data (auth0id varchar(32), systemid char(36),
    datasetid varchar(32), new_timeseries longblob, new_statistics longblob,
    new_version varchar(32), new_system_hash char(32))
    comment 'Update the timeseries and stats data'
    modifies sql data sql security definer
  begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean;
    set allowed = check_users_system(auth0id, systemid) and exists(
      select 1 from system_data where system_id = binid and dataset = datasetid
      );

    if allowed then
      update system_data set version = new_version,
        system_hash = unhex(new_system_hash),
        timeseries = new_timeseries, statistics = new_statistics
	where system_id = binid and dataset = datasetid;
    else
      signal sqlstate '42000' set message_text = 'Updating system data denied',
        mysql_errno = 1142;
    end if;    
  end;
grant update, select(system_id, dataset) on system_data to 'update_objects'@'localhost';
grant execute on procedure `update_system_data` to 'update_objects'@'localhost';
grant execute on procedure `update_system_data` to 'apiuser'@'%';

-- get data status
create definer = 'select_objects'@'localhost'
  procedure get_system_data_status (auth0id varchar(32), systemid char(36),
    datasetin varchar(32))
    comment 'Check the status of the system data'
    reads sql data sql security definer
  begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));
    declare row_present boolean;
    declare timeseries_status boolean default FALSE;
    declare stats_status boolean default FALSE;

    if allowed then
      set row_present = exists(
        select 1 from system_data where system_id = binid and dataset = datasetin);
      set timeseries_status = exists(
        select 1 from system_data where system_id = binid and dataset = datasetin
	and timeseries is not null);
      set stats_status = exists(
        select 1 from system_data where system_id = binid and dataset = datasetin
	and statistics is not null);	
      if not row_present then
        select 'missing' as status;
      else
        if timeseries_status and stats_status then
          select 'complete' as status;
        elseif timeseries_status and not stats_status then
          select 'statistics missing' as status;
        elseif not timeseries_status and stats_status then
          select 'timeseries missing' as status;
        else
  	  select 'prepared' as status;
	end if;
      end if;
    else
      signal sqlstate '42000' set message_text = 'Getting system data status denied',
        mysql_errno = 1142;
    end if;        
  end;
grant execute on procedure `get_system_data_status` to 'select_objects'@'localhost';
grant execute on procedure `get_system_data_status` to 'apiuser'@'%';


create procedure _add_example_data_1()
  modifies sql data
begin
  set @sysid = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1);
  set @extime = timestamp('2020-12-01 01:23');
  insert into system_data (system_id, dataset, created_at, modified_at) values (
    @sysid, 'nsrdb_2019', @extime, @extime);
end;


drop procedure add_example_data;
create procedure add_example_data()
begin
  call _add_example_data_0();
  call _add_example_data_1();
end;


-- migrate:down
drop procedure add_example_data;
create procedure add_example_data()
begin;
  call _add_example_data_0();
end;
drop procedure _add_example_data_1();
drop procedure get_system_data_status;
drop procedure update_system_data;
drop procedure create_system_data;
drop procedure get_system_statistics;
drop procedure get_system_timeseries;
drop table system_data;

