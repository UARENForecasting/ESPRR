-- migrate:up
create table system_groups (
  id binary(16) not null default (uuid_to_bin(uuid(), 1)),
  user_id binary(16) not null,
  name varchar(128) not null,
  created_at timestamp not null default current_timestamp,
  modified_at timestamp not null default current_timestamp on update current_timestamp,
  primary key (id),
  unique system_user_name_key (user_id, name),
  key systems_user_id_key (user_id),
  foreign key (user_id)
    references users(id)
    on delete cascade on update restrict
) engine=innodb row_format=compressed;

create table system_group_mapping (
  group_id binary(16) not null,
  system_id binary(16) not null,
  created_at timestamp not null default current_timestamp,
  primary key (group_id, system_id),
  foreign key (group_id)
    references system_groups(id)
    on delete cascade on update restrict,
  foreign key systems(system_id)
    references systems(id)
    on delete cascade on update restrict
) engine=innodb row_format=compressed;

create definer = 'select_objects'@'localhost'
  function check_users_system_group (auth0id varchar(32), groupid char(36))
    returns boolean
    comment 'Check if the system exists and belongs to user'
    reads sql data sql security definer
  begin
    return exists(select 1 from system_groups where id = uuid_to_bin(groupid, 1)
                                              and user_id = get_user_binid(auth0id));
  end;

grant execute on function `check_users_system_group` to 'select_objects'@'localhost';
grant execute on function `check_users_system_group` to 'insert_objects'@'localhost';
grant execute on function `check_users_system_group` to 'delete_objects'@'localhost';

-- get a group of systems
create definer = 'select_objects'@'localhost'
  procedure get_system_group(auth0id varchar(32), groupid char(36))
    comment 'Get the definition for a system group'
    reads sql data sql security definer
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
  end;

grant select on system_groups to 'select_objects'@'localhost';
grant execute on procedure `get_system_group` to 'select_objects'@'localhost';
grant execute on procedure `get_system_group` to 'apiuser'@'%';

-- list system_groups
create definer = 'select_objects'@'localhost'
  procedure list_system_groups (auth0id varchar(32))
    comment 'List all user system groups'
    reads sql data sql security definer
  begin
    select bin_to_uuid(id, 1) as group_id, bin_to_uuid(user_id, 1) as user_id,
           name, created_at, modified_at from system_groups
     where user_id = get_user_binid(auth0id);
  end;

grant execute on procedure `list_system_groups` to 'select_objects'@'localhost';
grant execute on procedure `list_system_groups` to 'apiuser'@'%';


-- Get the systems of a group
create definer = 'select_objects'@'localhost'
  procedure get_group_systems(auth0id varchar(32), groupid varchar(36))
    comment 'Get name and id of each system that belongs to a group'
    reads sql data sql security definer
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
  end;

grant select on `system_group_mapping` to 'select_objects'@'localhost';
grant execute on procedure `get_group_systems` to 'select_objects'@'localhost';
grant execute on procedure `get_group_systems` to 'apiuser'@'%';

-- create system group
create definer = 'insert_objects'@'localhost'
  procedure create_system_group (auth0id varchar(32), name varchar(128))
    comment 'Create a new system group'
    modifies sql data sql security definer
  begin
    declare groupid char(36) default (uuid());
    declare binid binary(16) default (uuid_to_bin(groupid, 1));
    insert into system_groups (id, user_id, name) values (
      binid, get_user_binid(auth0id), name);
    select groupid as group_id;
  end;

grant insert on system_groups to 'insert_objects'@'localhost';
grant execute on function `get_user_binid` to 'insert_objects'@'localhost';
grant execute on procedure `create_system_group` to 'insert_objects'@'localhost';
grant execute on procedure `create_system_group` to 'apiuser'@'%';

-- update system group name
create definer = 'update_objects'@'localhost'
  procedure update_system_group (auth0id varchar(32), groupid char(36), new_name varchar(128))
    comment 'Update system group'
    modifies sql data sql security definer
  begin

    declare allowed boolean default(check_users_system_group(auth0id, groupid));
    declare binid binary(16) default (uuid_to_bin(groupid, 1));
    if allowed then
        update system_groups set name = new_name where id = binid;
    else
        signal sqlstate '42000' set message_text = 'Updating system group not allowed',
          mysql_errno = 1142;
    end if;
  end;

grant select, update on system_groups to 'update_objects'@'localhost';
grant execute on function `check_users_system_group` to 'update_objects'@'localhost';
grant execute on procedure `update_system_group` to 'update_objects'@'localhost';
grant execute on procedure `update_system_group` to 'apiuser'@'%';


-- add a system to a group
create definer = 'insert_objects'@'localhost'
  procedure add_system_to_group(auth0id varchar(32), systemid char(36), groupid char(128))
    comment 'Add a system to a group'
    modifies sql data sql security definer
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
  end;

grant insert on system_group_mapping to 'insert_objects'@'localhost';
grant execute on procedure `add_system_to_group` to 'insert_objects'@'localhost';
grant execute on procedure `add_system_to_group` to 'apiuser'@'%';

-- remove a system from a group
create definer = 'delete_objects'@'localhost'
  procedure remove_system_from_group(auth0id varchar(32), systemid char(36), groupid char(128))
    comment 'Add a system to a group'
    modifies sql data sql security definer
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
  end;

grant select, delete on system_group_mapping to 'delete_objects'@'localhost';
grant execute on function `check_users_system_group` to 'delete_objects'@'localhost';
grant execute on procedure `remove_system_from_group` to 'delete_objects'@'localhost';
grant execute on procedure `remove_system_from_group` to 'apiuser'@'%';

-- delete system
create definer = 'delete_objects'@'localhost'
  procedure delete_system_group (auth0id varchar(32), groupid char(36))
    comment 'Delete a system group'
    modifies sql data sql security definer
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
  end;

grant select(id), delete on system_groups to 'delete_objects'@'localhost';
grant execute on function `check_users_system_group` to 'delete_objects'@'localhost';
grant execute on procedure `delete_system_group` to 'delete_objects'@'localhost';
grant execute on procedure `delete_system_group` to 'apiuser'@'%';


-- Updates the example timeseries to correctly conform to the expected
drop procedure _add_example_data_1;

DELETE FROM system_data
    WHERE system_id = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1)
    AND dataset = "NSRDB_2019";

create procedure _add_example_data_1()
  modifies sql data
begin
  set @sysid = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1);
  set @extime = timestamp('2020-12-01 01:23');
  set @syshash = (select unhex(md5(definition)) from systems where id = @sysid);
  insert into system_data (system_id, dataset, version, system_hash, timeseries, statistics, created_at, modified_at) values (
    @sysid, 'NSRDB_2019', 'v0.1', unhex('29b4855d70dc37601bb31323f9703cf1'),
    from_base64('QVJST1cxAAD/////aAQAABAAAAAAAAoADgAGAAUACAAKAAAAAAEEABAAAAAAAAoADAAAAAQACAAKAAAANAMAAAQAAAABAAAADAAAAAgADAAEAAgACAAAAAgAAAAQAAAABgAAAHBhbmRhcwAA/gIAAHsiaW5kZXhfY29sdW1ucyI6IFtdLCAiY29sdW1uX2luZGV4ZXMiOiBbeyJuYW1lIjogbnVsbCwgImZpZWxkX25hbWUiOiBudWxsLCAicGFuZGFzX3R5cGUiOiAidW5pY29kZSIsICJudW1weV90eXBlIjogIm9iamVjdCIsICJtZXRhZGF0YSI6IHsiZW5jb2RpbmciOiAiVVRGLTgifX1dLCAiY29sdW1ucyI6IFt7Im5hbWUiOiAidGltZSIsICJmaWVsZF9uYW1lIjogInRpbWUiLCAicGFuZGFzX3R5cGUiOiAiZGF0ZXRpbWV0eiIsICJudW1weV90eXBlIjogImRhdGV0aW1lNjRbbnNdIiwgIm1ldGFkYXRhIjogeyJ0aW1lem9uZSI6ICJFdGMvR01UKzcifX0sIHsibmFtZSI6ICJhY19wb3dlciIsICJmaWVsZF9uYW1lIjogImFjX3Bvd2VyIiwgInBhbmRhc190eXBlIjogImZsb2F0MzIiLCAibnVtcHlfdHlwZSI6ICJmbG9hdDMyIiwgIm1ldGFkYXRhIjogbnVsbH0sIHsibmFtZSI6ICJjbGVhcnNreV9hY19wb3dlciIsICJmaWVsZF9uYW1lIjogImNsZWFyc2t5X2FjX3Bvd2VyIiwgInBhbmRhc190eXBlIjogImZsb2F0MzIiLCAibnVtcHlfdHlwZSI6ICJmbG9hdDMyIiwgIm1ldGFkYXRhIjogbnVsbH0sIHsibmFtZSI6ICJkY19wb3dlciIsICJmaWVsZF9uYW1lIjogImRjX3Bvd2VyIiwgInBhbmRhc190eXBlIjogImZsb2F0MzIiLCAibnVtcHlfdHlwZSI6ICJmbG9hdDMyIiwgIm1ldGFkYXRhIjogbnVsbH1dLCAiY3JlYXRvciI6IHsibGlicmFyeSI6ICJweWFycm93IiwgInZlcnNpb24iOiAiNC4wLjEifSwgInBhbmRhc192ZXJzaW9uIjogIjEuMy4wIn0AAAQAAAC8AAAAdAAAADgAAAAEAAAA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'),
    from_base64('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'),

    @extime, @extime
    );
end;
create procedure _add_example_data_2()
  modifies sql data
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
end;

drop procedure add_example_data;

create procedure add_example_data()
begin
  call _add_example_data_0();
  call _add_example_data_1();
  call _add_example_data_2();
end;

-- migrate:down
drop procedure add_example_data;
create procedure add_example_data()
begin
  call _add_example_data_0();
  call _add_example_data_1();
end;

drop procedure delete_system_group;
drop procedure create_system_group;
drop procedure update_system_group;
drop procedure list_system_groups;
drop procedure get_system_group;
drop procedure get_group_systems;
drop procedure add_system_to_group;
drop procedure remove_system_from_group;
drop function check_users_system_group;
drop table system_group_mapping;
drop table system_groups;
drop procedure _add_example_data_2;
drop procedure _add_example_data_1;

DELETE FROM system_data
    WHERE system_id = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1)
    AND dataset = "NSRDB_2019";

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
