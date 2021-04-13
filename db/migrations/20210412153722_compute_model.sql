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
  function get_system_data_status (binid binary(16), datasetin varchar(32))
    returns varchar(32)
    reads sql data sql security definer
  begin
    declare timeseries_status boolean default (exists(
      select 1 from system_data where system_id = binid and dataset = datasetin
      and timeseries is not null));
    declare stats_status boolean default (exists(
      select 1 from system_data where system_id = binid and dataset = datasetin
      and statistics is not null));	

    if timeseries_status and stats_status then
      return 'complete';
    elseif timeseries_status and not stats_status then
      return 'statistics missing';
    elseif not timeseries_status and stats_status then
      return 'timeseries missing';
    else
      return 'prepared';
    end if;
  end;
grant execute on function `get_system_data_status` to 'select_objects'@'localhost';


create definer = 'select_objects'@'localhost'
  procedure get_system_data_meta (auth0id varchar(32), systemid char(36),
    datasetid varchar(32))
    comment 'Get the system data metadata'
    reads sql data sql security definer
  begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));
    declare row_present boolean default (exists(
      select 1 from system_data where system_id = binid and dataset = datasetid));


    if allowed and row_present then
      select bin_to_uuid(system_id, 1) as system_id,
        dataset, version, hex(system_hash) as system_hash,
        get_system_data_status(binid, datasetid) as status,
        created_at, modified_at
      from system_data where system_id = binid and dataset = datasetid;
    else
      signal sqlstate '42000' set message_text = 'Getting system data metadata denied',
        mysql_errno = 1142;
    end if;
  end;
grant execute on procedure `get_system_data_meta` to 'select_objects'@'localhost';
grant execute on procedure `get_system_data_meta` to 'apiuser'@'%';


create definer = 'select_objects'@'localhost'
  procedure get_system_hash(auth0id varchar(32), systemid char(36))
  reads sql data sql security definer
begin
  declare binid binary(16) default (uuid_to_bin(systemid, 1));
  declare allowed boolean default (check_users_system(auth0id, systemid));

  if allowed then
    select md5(definition) as system_hash from systems where id = binid;
  else
    signal sqlstate '42000' set message_text = 'Getting system hash denied',
      mysql_errno = 1142;
  end if;
end;
grant execute on procedure `get_system_hash` to 'select_objects'@'localhost';
grant execute on procedure `get_system_hash` to 'apiuser'@'%';


create procedure _add_example_data_1()
  modifies sql data
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
begin
  call _add_example_data_0();
end;
drop procedure get_system_hash;
drop procedure _add_example_data_1;
drop procedure get_system_data_meta;
drop function get_system_data_status;
drop procedure update_system_data;
drop procedure create_system_data;
drop procedure get_system_statistics;
drop procedure get_system_timeseries;
drop table system_data;

