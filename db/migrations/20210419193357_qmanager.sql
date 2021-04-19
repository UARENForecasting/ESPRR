-- migrate:up
create definer = 'select_objects'@'localhost'
  procedure list_system_data_status()
    reads sql data sql security definer
  begin
    select bin_to_uuid(system_id, 1) as system_id, dataset,
      get_system_data_status(system_id, dataset) as status, version,
      (system_hash != unhex(md5(systems.definition))) as hash_changed,
      users.auth0_id as user
    from system_data join (systems, users) on systems.id = system_data.system_id
    and systems.user_id = users.id;
  end;

grant execute on procedure `list_system_data_status` to 'select_objects'@'localhost';
grant execute on procedure `list_system_data_status` to 'qmanager'@'%';


create definer = 'update_objects'@'localhost'
  procedure report_failure (systemid char(36), datasetname varchar(32), newerror JSON)
    modifies sql data sql security definer
  begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));

    update system_data set error = newerror where system_id = binid and dataset = datasetname;
  end;

grant execute on procedure `report_failure` to 'update_objects'@'localhost';
grant execute on procedure `report_failure` to 'qmanager'@'%';

-- migrate:down
drop procedure `report_failure`;
drop procedure `list_system_data_status`;
