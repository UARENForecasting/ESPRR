-- migrate:up
create procedure _add_example_data_0()
  modifies sql data
begin
  set @userid = uuid_to_bin('17fbf1c6-34bd-11eb-af43-f4939feddd82', 1);
  set @otheruser = uuid_to_bin('972084d4-34cd-11eb-8f13-f4939feddd82', 1);
  set @sysid = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1);
  set @othersysid = uuid_to_bin('6513485a-34cd-11eb-8f13-f4939feddd82', 1);
  set @extime = timestamp('2020-12-01 01:23');
  set @sysdef = '{
       "name": "Test PV System",
       "boundary": {
           "nw_corner": {"latitude": 34.9, "longitude": -112.9},
           "se_corner": {"latitude": 33.0, "longitude": -111.0}
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
end;


create procedure _remove_example_data_0()
  modifies sql data
begin
  set @userid = uuid_to_bin('17fbf1c6-34bd-11eb-af43-f4939feddd82', 1);
  set @sysid = uuid_to_bin('6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9', 1);
  set @othersysid = uuid_to_bin('6513485a-34cd-11eb-8f13-f4939feddd82', 1);
  set @otheruser = uuid_to_bin('972084d4-34cd-11eb-8f13-f4939feddd82', 1);

  delete from systems where id = @sysid;
  delete from systems where id = @othersysid;
  delete from users where id = @userid;
  delete from users where id = @otheruser;
end;

create procedure add_example_data ()
  modifies sql data
begin
  CALL _add_example_data_0;
end;

create procedure remove_example_data ()
  modifies sql data
begin
  call _remove_example_data_0;
end;

-- migrate:down
drop procedure _remove_example_data_0;--
drop procedure remove_example_data;
drop procedure _add_example_data_0;
drop procedure add_example_data;
