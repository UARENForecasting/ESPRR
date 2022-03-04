<template>
  <div class="groups" v-if="$auth.isAuthenticated">
    <h2>Groups</h2>
    <router-link :to="{ name: 'New System' }" class="new-system-link"
      >Create New Group</router-link
    >
    <hr />
    <div class="grid">
      <div class="groups-table">
        <table v-if="groups.length > 0">
          <thead>
            <tr>
              <th>Name</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-bind:class="{
                'selected-site':
                  selected && group.object_id == selected.object_id,
              }"
              v-for="group of groups"
              :key="group.object_id"
              role="button"
              @click="setSelected(group)"
            >
              <td>{{ group.definition.name }}</td>
            </tr>
          </tbody>
        </table>
        <!-- update with link to system form -->
        <p v-else>
          No Systems yet.
          <router-link :to="{ name: 'New System' }" class="new-system-link"
            >Create a new System</router-link
          >
        </p>
      </div>
      <div class="details">
        <template v-if="selected">
          <h3>Group Details</h3>
          <!--
          <router-link
            tag="button"
            :to="{
              name: 'Update System',
              params: { systemId: selected.object_id },
              query: { returnTo: 'groups' },
            }"
            >
            -->
          <a>Update Group</a>
          <!--</router-link>-->
          <!--<button class="delete-system" @click="showDeleteDialog = true">
            Delete Group
          </button>-->
          <a>Delete System</a>
          <p><b>Name: </b>{{ selected.definition.name }}</p>
          <ul class="details-list">
            <li
              v-for="system of selected.definition.systems"
              :key="system.object_id"
            >
              {{ system.definition.name }}
            </li>
            <!-- TODO: put the group overview stuff here -->
          </ul>
          <system-map
            :system="selected.definition"
            :all_systems="selected.definition.systems"
            @new-selection="setSelected"
          />
        </template>
      </div>
    </div>
    <transition name="fade">
      <div v-if="showDeleteDialog" id="delete-dialog">
        <div class="modal-block">
          <p>
            Are you sure you want to delete the system
            {{ selected.definition.name }}?
          </p>
          <button class="confirm-deletion" @click="deleteSystem">Yes</button>
          <button class="cancel-deletion" @click="showDeleteDialog = false">
            Cancel
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator";
import { StoredPVSystem, StoredPVSystemGroup } from "@/models";

import * as SystemsAPI from "@/api/systems";
import SystemMap from "@/components/Map.vue";

Vue.component("system-map", SystemMap);

let some_systems = [
  {
    object_id: "92688f97-9bee-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T19:09:10+00:00",
    modified_at: "2022-03-04T19:09:10+00:00",
    definition: {
      name: "New System",
      boundary: {
        nw_corner: {
          latitude: 33.47725534446616,
          longitude: -112.10808312274808,
        },
        se_corner: {
          latitude: 33.47569940977952,
          longitude: -112.10621776166168,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
  {
    object_id: "1524579a-9c05-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T21:50:18+00:00",
    modified_at: "2022-03-04T21:50:18+00:00",
    definition: {
      name: "New System 1",
      boundary: {
        nw_corner: {
          latitude: 33.47614197858108,
          longitude: -112.16302036131157,
        },
        se_corner: {
          latitude: 33.47458604389473,
          longitude: -112.16115502419449,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
  {
    object_id: "17bdf125-9c05-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T21:50:22+00:00",
    modified_at: "2022-03-04T21:50:22+00:00",
    definition: {
      name: "New System 2",
      boundary: {
        nw_corner: {
          latitude: 33.447604570515075,
          longitude: -111.93297031768007,
        },
        se_corner: {
          latitude: 33.446048635836284,
          longitude: -111.9311055944852,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
];

let some_more_systems = [
  {
    object_id: "1c444276-9c05-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T21:50:30+00:00",
    modified_at: "2022-03-04T21:50:30+00:00",
    definition: {
      name: "New System 3",
      boundary: {
        nw_corner: {
          latitude: 33.56002104168809,
          longitude: -112.0283285405074,
        },
        se_corner: {
          latitude: 33.5584651069795,
          longitude: -112.0264613938828,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
  {
    object_id: "1f27b96a-9c05-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T21:50:35+00:00",
    modified_at: "2022-03-04T21:50:35+00:00",
    definition: {
      name: "New System 4",
      boundary: {
        nw_corner: {
          latitude: 33.49369608811077,
          longitude: -112.02832487957924,
        },
        se_corner: {
          latitude: 33.49214015341977,
          longitude: -112.0264591643916,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
  {
    object_id: "23108cc5-9c05-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T21:50:41+00:00",
    modified_at: "2022-03-04T21:50:41+00:00",
    definition: {
      name: "New System 5",
      boundary: {
        nw_corner: {
          latitude: 33.17229979504934,
          longitude: -111.93479395902408,
        },
        se_corner: {
          latitude: 33.170743860443224,
          longitude: -111.9329351141132,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
  {
    object_id: "26ddb97d-9c05-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T21:50:48+00:00",
    modified_at: "2022-03-04T21:50:48+00:00",
    definition: {
      name: "New System 6",
      boundary: {
        nw_corner: {
          latitude: 33.42468531239764,
          longitude: -111.72325569978534,
        },
        se_corner: {
          latitude: 33.42312937772493,
          longitude: -111.72139146902272,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
  {
    object_id: "2d6c30d5-9c05-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T21:50:59+00:00",
    modified_at: "2022-03-04T21:50:59+00:00",
    definition: {
      name: "New System 7",
      boundary: {
        nw_corner: {
          latitude: 33.41769571762809,
          longitude: -112.36881572254464,
        },
        se_corner: {
          latitude: 33.41613978295722,
          longitude: -112.36695164184606,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
  {
    object_id: "322d1035-9c05-11ec-8c79-0242ac110002",
    object_type: "system",
    created_at: "2022-03-04T21:51:07+00:00",
    modified_at: "2022-03-04T21:51:07+00:00",
    definition: {
      name: "New System 8",
      boundary: {
        nw_corner: {
          latitude: 33.55497978499569,
          longitude: -112.16002058692186,
        },
        se_corner: {
          latitude: 33.55342385028843,
          longitude: -112.15815354926356,
        },
      },
      ac_capacity: 1,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: { tilt: 0, azimuth: 180 },
    },
  },
];

@Component
export default class Groups extends Vue {
  //systems!: Array<StoredPVSystem>;
  groups!: Array<StoredPVSystemGroup>;
  selected!: Record<string, any>;
  showDeleteDialog!: boolean;

  created(): void {
    // When the component is created, load the systems list.
    this.getSystems();
    console.log("groups view created");
  }

  data(): Record<string, any> {
    return {
      groups: [],
      selected: null,
      showDeleteDialog: false,
    };
  }

  async getSystems(): Promise<void> {
    // Load the the list of systems from the api
    // const token = await this.$auth.getTokenSilently();
    // this.systems = await SystemsAPI.listSystems(token);
    this.groups = [
      {
        created_at: "now",
        modified_at: "then",
        object_id: "shvifty-five",
        object_type: "system_group",
        definition: {
          name: "Group 1",
          systems: some_systems,
        },
      },
      {
        created_at: "now",
        modified_at: "then",
        object_id: "shvifty-six",
        object_type: "system_group",
        definition: {
          name: "Group 2",
          systems: some_more_systems,
        },
      },
    ];
    if (this.groups.length) {
      this.setSelected(this.groups[0]);
    }
  }
  async deleteGroup(): Promise<void> {
    if (this.selected != null) {
      const token = await this.$auth.getTokenSilently();
      //SystemsAPI.deleteSystem(token, this.selected.object_id)
      //  .then(() => {
      //    this.getSystems();
      //    this.showDeleteDialog = false;
      //  })
      //  .catch((error: any) => {
      //    // TODO: display errors to user
      //    console.error(error);
      //    this.showDeleteDialog = false;
      //  });
    }
  }
  setSelected(selectedSystem: Record<string, any>): void {
    this.selected = selectedSystem;
  }
  get notSelectedSystems(): Array<StoredPVSystemGroup> {
    return this.groups.filter((group: StoredPVSystemGroup) => {
      return group.object_id != this.selected.object_id;
    });
  }
}
</script>
<style scoped>
div.grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
}

.details,
.systems-table {
  display: grid-item;
}

.details {
  padding: 0 1em;
}

table {
  width: 100%;
}

thead tr {
  border-bottom: 1px solid black;
  background-color: white;
}

tbody tr:hover {
  cursor: pointer;
  background: #eee;
}

tr {
  display: grid;
  padding: 0.5em;
  grid-template-columns: 2fr 2fr 1fr;
  border-bottom: 1px solid #ccc;
}

th {
  text-align: left;
}

td:first-child,
th:first-child {
  padding-left: 0;
}

td,
th {
  display: grid;
  padding: 0 1em;
}

tr.selected-site {
  background-color: #ccc;
}

table {
  border-spacing: 0;
}
.new-system-link {
  display: inline-block;
}
#delete-dialog {
  position: fixed;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  display: block;
  background-color: rgba(0, 0, 0, 0.5);
}
#delete-dialog .modal-block {
  width: 500px;
  margin: 35vh auto;
  padding: 2em;
  border: 1px solid #000;
  background-color: #fff;
}
#delete-dialog button {
  display: inline-block;
}
</style>
