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
  foreign key systems(id)
    references system_groups(id)
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

-- get a group of systems
create definer = 'select_objects'@'localhost'
  procedure get_system_groups (auth0id varchar(32), groupid char(36))
    comment 'Get the definition for a system group'
    reads sql data sql security definer
  begin
    declare binid binary(16) default (uuid_to_bin(systemid, 1));
    declare allowed boolean default (check_users_system(auth0id, systemid));

    if allowed then
      select bin_to_uuid(id, 1) as groupid, bin_to_uuid(user_id, 1) as user_id,
      name, definition, created_at, modified_at from systems where id = binid;
    else
      signal sqlstate '42000' set message_text = 'System inaccessible',
        mysql_errno = 1142;
    end if;
  end;

grant select on system_groups to 'select_objects'@'localhost';
grant execute on procedure `get_system_groups` to 'select_objects'@'localhost';
grant execute on procedure `get_system_groups` to 'apiuser'@'%';

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


create definer = 'select_objects'@'localhost'
  function get_group_systems(auth0id varchar(32), groupid varchar(36))
  comment 'Get name and id of each system that belongs to a group'
  begin
    select bin_to_uuid(systems.id, 1) as object_id,
           bin_to_uuid(systems.user_id, 1) as user_id,
           name,
           definition,
           created_at,
           modified_at
    from systems WHERE id in (
        select system_id
        from system_group_mapping
        where group_id = uuid_to_bin(groupid, 1);
    );
  end;

grant execute on function `get_group_systems` to 'select_objects'@'localhost';

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

grant insert on systems to 'insert_objects'@'localhost';
grant execute on function `get_user_binid` to 'insert_objects'@'localhost';
grant execute on procedure `create_system` to 'insert_objects'@'localhost';
grant execute on procedure `create_system` to 'apiuser'@'%';


-- TODO: Complete system grouping code
-- update system
create definer = 'insert_objects'@'localhost'
  procedure add_system_to_group(auth0id varchar(32), systemid char(36), groupid char(128))
    comment 'Add a system to a group'
    modifies sql data sql security definer
  begin
    declare bin_system_id binary(16) default (uuid_to_bin(systemid, 1));
    declare bin_group_id binary(16) default (uuid_to_bin(group, 1));

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

-- delete system
create definer = 'delete_objects'@'localhost'
  procedure delete_system (auth0id varchar(32), systemid char(36))
    comment 'Delete a system'
    modifies sql data sql security definer
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
  end;

grant select(id), delete on systems to 'delete_objects'@'localhost';
grant execute on function `check_users_system` to 'delete_objects'@'localhost';
grant execute on function `get_user_binid` to 'delete_objects'@'localhost';
grant execute on procedure `delete_system` to 'delete_objects'@'localhost';
grant execute on procedure `delete_system` to 'apiuser'@'%';

-- migrate:down
drop procedure delete_system;
drop procedure update_system;
drop procedure create_system;
drop procedure list_systems;
drop procedure get_system;
drop function check_users_system;
drop table systems;
