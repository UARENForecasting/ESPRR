<template>
  <div class="groups" v-if="$auth.isAuthenticated">
    <h2>Groups</h2>
    <router-link :to="{ name: 'New Group' }" class="new-group-link"
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
          No System Groups yet.
          <router-link :to="{ name: 'New Group' }" class="new-system-link"
            >Create a new Group</router-link
          >
        </p>
      </div>
      <div class="details">
        <template v-if="selected">
          <h3>Group Details</h3>
          <router-link
            tag="button"
            :to="{
              name: 'Update Group',
              params: { groupId: selected.object_id },
              query: { returnTo: 'groups' },
            }"
          >
            Update Group
          </router-link>
          <button class="delete-group" @click="showDeleteDialog = true">
            Delete Group
          </button>
          <p><b>Name: </b>{{ selected.definition.name }}</p>
          <b>Systems:</b>
          <ul class="details-list" style="list-style: square;">
            <li
              v-for="(system, i) of selected.definition.systems"
              :key="system.object_id"
              :style="{ color: getColor(i), fontSize: '20pt' }"
            >
              <span style="color: #000;font-size: 12pt;">{{ system.definition.name }}</span>
            </li>
            <!-- TODO: put the group overview stuff here -->
          </ul>
          <system-map
            :systems="selected.definition.systems"
            @new-selection="setSelected"
          />
        </template>
      </div>
    </div>
    <transition name="fade">
      <div v-if="showDeleteDialog" id="delete-dialog">
        <div class="modal-block">
          <p>
            Are you sure you want to delete the group
            {{ selected.definition.name }}?
          </p>
          <button class="confirm-deletion" @click="deleteGroup">Yes</button>
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
import { StoredPVSystemGroup } from "@/models";

import * as GroupsAPI from "@/api/systemGroups";
import SystemMap from "@/components/Map.vue";
import GetColor from "@/utils/Colors";

Vue.component("system-map", SystemMap);

@Component
export default class Groups extends Vue {
  groups!: Array<StoredPVSystemGroup>;
  selected!: Record<string, any>;
  showDeleteDialog!: boolean;

  created(): void {
    // When the component is created, load the systems list.
    this.getSystemGroups();
    console.log("groups view created");
  }

  data(): Record<string, any> {
    return {
      groups: [],
      selected: null,
      showDeleteDialog: false,
    };
  }

  async getSystemGroups(): Promise<void> {
    // Load the the list of systems from the api
    const token = await this.$auth.getTokenSilently();
    this.groups = await GroupsAPI.listSystemGroups(token);
    if (this.groups.length) {
      this.setSelected(this.groups[0]);
    }
  }
  async deleteGroup(): Promise<void> {
    if (this.selected != null) {
      const token = await this.$auth.getTokenSilently();
      GroupsAPI.deleteSystemGroup(token, this.selected.object_id)
        .then(() => {
          this.getSystemGroups();
          this.showDeleteDialog = false;
        })
        .catch((error: any) => {
          // TODO: display errors to user
          console.error(error);
          this.showDeleteDialog = false;
        });
    }
  }
  async setSelected(selectedSystemGroup: Record<string, any>): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    this.selected = await GroupsAPI.getSystemGroup(
      token,
      selectedSystemGroup.object_id
    );
  }
  get notSelectedSystemGroups(): Array<StoredPVSystemGroup> {
    return this.groups.filter((group: StoredPVSystemGroup) => {
      return group.object_id != this.selected.object_id;
    });
  }
  getColor(seed: number): string {
    return GetColor(seed);
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
