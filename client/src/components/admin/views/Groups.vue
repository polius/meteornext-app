<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">GROUPS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newGroup()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editGroup()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteGroup()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:items="props">
          <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
          <td>{{ props.item.name }}</td>
          <td>{{ props.item.description }}</td>
        </template>
        <template v-slot:no-results>
          <v-alert :value="true" color="error" icon="warning" style="margin-top:15px;">
            Your search for "{{ search }}" found no results.
          </v-alert>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="1280px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="mode!='delete'" style="margin-bottom:10px;">
                <v-form ref="form" v-model="dialog_valid">
                  <!-- METADATA -->
                  <div class="title font-weight-regular">Metadata</div>
                  <v-text-field v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-text-field v-model="item.description" :rules="[v => !!v || '']" label="Description" required style="padding-top:0px; margin-top:0px;"></v-text-field>

                  <!-- DEPLOYMENTS -->
                  <div class="title font-weight-regular" style="margin-top:5px;">Deployments</div>

                  <!-- environments -->
                  <v-card style="margin-bottom:10px;">
                    <v-toolbar flat dense style="margin-top:20px;">
                      <v-toolbar-title class="white--text">Environments</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                        <v-btn text @click='new_environment()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                        <v-btn v-if="environment_selected.length == 1" text @click="edit_environment()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                        <v-btn v-if="environment_selected.length > 0" text @click='delete_environment()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                      </v-toolbar-items>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-data-table v-model="environment_selected" :headers="environment_headers" :items="environment_items" :search="environment_search" item-key="name" hide-default-header hide-default-footer show-select class="elevation-1">
                      <template v-slot:items="props">
                        <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
                        <td>{{ props.item.name }}</td>
                      </template>
                    </v-data-table>
                  </v-card>

                  <!-- regions -->
                  <v-card style="margin-bottom:10px;">
                    <v-toolbar flat dense style="margin-top:10px;">
                      <v-toolbar-title class="white--text">Regions</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                        <v-btn text @click='new_region()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                        <v-btn v-if="region_selected.length == 1" text @click="edit_region()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                        <v-btn v-if="region_selected.length > 0" text @click='delete_region()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                      </v-toolbar-items>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-data-table v-model="region_selected" :headers="region_headers" :items="region_items" item-key="name" :hide-default-header="region_items.length == 0" hide-default-footer show-select class="elevation-1">
                      <template v-slot:items="props">
                        <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
                        <td>{{ props.item.name }}</td>
                        <td>{{ props.item.environment }}</td>
                        <td>{{ props.item.cross_region }}</td>
                        <td>{{ props.item.hostname }}</td>
                        <td>{{ props.item.username }}</td>
                        <td>{{ props.item.password }}</td>
                      </template>
                    </v-data-table>
                  </v-card>

                  <!-- servers -->
                  <v-card style="margin-bottom:10px;">
                    <v-toolbar flat dense style="margin-top:10px;">
                      <v-toolbar-title class="white--text">Servers</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                        <v-btn text @click='new_server()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                        <v-btn v-if="server_selected.length == 1" text @click="edit_server()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                        <v-btn v-if="server_selected.length > 0" text @click='delete_server()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                      </v-toolbar-items>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-data-table v-model="server_selected" :headers="server_headers" :items="server_items" item-key="name" :hide-default-header="server_items.length == 0" hide-default-footer show-select class="elevation-1">
                      <template v-slot:items="props">
                        <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
                        <td>{{ props.item.name }}</td>
                        <td>{{ props.item.environment }}</td>
                        <td>{{ props.item.region }}</td>
                        <td>{{ props.item.hostname }}</td>
                        <td>{{ props.item.username }}</td>
                        <td>{{ props.item.password }}</td>
                      </template>
                    </v-data-table>
                  </v-card>

                  <!-- auxiliary connections -->
                  <v-card style="margin-bottom:10px;">
                    <v-toolbar flat dense style="margin-top:10px;">
                      <v-toolbar-title class="white--text">Auxiliary Connections</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                        <v-btn text @click='new_auxiliary()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                        <v-btn v-if="auxiliary_selected.length == 1" text @click="edit_auxiliary()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                        <v-btn v-if="auxiliary_selected.length > 0" text @click='delete_auxiliary()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                      </v-toolbar-items>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-data-table v-model="auxiliary_selected" :headers="auxiliary_headers" :items="auxiliary_items" item-key="name" :hide-default-header="auxiliary_items.length == 0" hide-default-footer show-select class="elevation-1">
                      <template v-slot:items="props">
                        <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
                        <td>{{ props.item.name }}</td>
                        <td>{{ props.item.hostname }}</td>
                        <td>{{ props.item.username }}</td>
                        <td>{{ props.item.password }}</td>
                      </template>
                    </v-data-table>
                  </v-card>

                  <!-- slack -->
                  <v-card>
                    <v-toolbar flat dense style="margin-top:10px;">
                      <v-toolbar-title class="white--text">Slack</v-toolbar-title>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-card-text style="padding-bottom:0px;">
                      <v-text-field v-model="slack_webhook" label="Webhook URL" required style="padding-top:0px;"></v-text-field>
                      <v-switch v-model="slack_enabled" label="Enable Notifications" style="margin-top:0px;"></v-switch>
                    </v-card-text>
                  </v-card>

                  <!-- amazon s3 -->
                  <v-card>
                    <v-toolbar flat dense style="margin-top:10px;">
                      <v-toolbar-title class="white--text">Amazon S3</v-toolbar-title>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-card-text style="padding-bottom:0px;">
                      <v-text-field v-model="s3_aws_access_key" label="AWS Access Key" style="padding-top:0px;"></v-text-field>
                      <v-text-field v-model="s3_aws_secret_access_key" label="AWS Secret Access Key" style="padding-top:0px;"></v-text-field>
                      <v-text-field v-model="s3_region_name" label="Region Name" hint="Example: eu-west-1" style="padding-top:0px;"></v-text-field>
                      <v-text-field v-model="s3_bucket_name" label="Bucket Name" style="padding-top:0px;"></v-text-field>
                      <v-switch v-model="s3_enabled" label="Enable Uploading Logs" style="margin-top:0px;"></v-switch>
                    </v-card-text>
                  </v-card>

                  <!-- web -->
                  <v-card>
                    <v-toolbar flat dense style="margin-top:10px;">
                      <v-toolbar-title class="white--text">Web</v-toolbar-title>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-card-text style="padding-bottom:0px;">
                      <v-text-field v-model="web_public_url" label="Public Web URL" required style="padding-top:0px;"></v-text-field>
                    </v-card-text>
                  </v-card>
                </v-form>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected groups?</div>
              </v-flex>

              <v-btn color="success" @click="submitGroup()">Confirm</v-btn>
              <v-btn color="error" @click="dialog=false" style="margin-left:10px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--
    +--------------+
    | ENVIRONMENTS |
    +--------------+
    -->
    <v-dialog v-model="environment_dialog" persistent max-width="768px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ environment_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="environment_mode!='delete'">
                <v-text-field ref="field" v-on:keyup.enter="confirm_environment()" v-model="environment_item.name" label="Environment Name" required></v-text-field>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="environment_mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected environments?</div>
              </v-flex>
              <v-btn color="success" @click="confirm_environment()">Confirm</v-btn>
              <v-btn color="error" @click="environment_dialog=false" style="margin-left:10px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--
    +---------+
    | REGIONS |
    +---------+
    -->
    <v-dialog v-model="region_dialog" persistent max-width="768px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ region_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="region_mode!='delete'">
                <!-- METADATA -->
                <div class="title font-weight-regular">Metadata</div>
                <v-text-field ref="field" v-model="region_item.name" label="Name" required></v-text-field>
                <v-select v-model="region_item.environment" :items="environments_list" label="Environment" required style="margin-top:0px; padding-top:0px;"></v-select>
                <!-- SSH -->
                <v-switch v-model="region_item.cross_region" label="Cross Region" style="margin-top:0px;"></v-switch>
                <div v-if="region_item.cross_region">
                  <div class="title font-weight-regular">SSH</div>
                  <v-text-field v-model="region_item.hostname" label="Hostname"></v-text-field>
                  <v-text-field v-model="region_item.username" label="Username" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="region_item.password" label="Password" style="padding-top:0px;"></v-text-field>
                  <v-textarea v-model="region_item.key" label="Private Key" style="padding-top:0px;"></v-textarea>
                </div>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="region_mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected regions?</div>
              </v-flex>
              <v-btn :loading="loading" color="success" @click="confirm_region()">Confirm</v-btn>
              <v-btn :disabled="loading" color="error" @click="region_dialog=false" style="margin-left:10px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--
    +---------+
    | SERVERS |
    +---------+
    -->
    <v-dialog v-model="server_dialog" persistent max-width="768px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ server_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="server_mode!='delete'">
                <!-- METADATA -->
                <div class="title font-weight-regular">Metadata</div>
                <v-text-field ref="field" v-model="server_item.name" label="Name" required></v-text-field>
                <v-select v-model="server_item.environment" :items="environments_list" label="Environment" required style="margin-top:0px; padding-top:0px;"></v-select>
                <v-select v-model="server_item.region" :items="regions_list" label="Region" required style="margin-top:0px; padding-top:0px;"></v-select>
                <!-- SQL -->
                <div class="title font-weight-regular" style="padding-top:10px;">SQL</div>
                <v-text-field v-model="server_item.hostname" label="Hostname"></v-text-field>
                <v-text-field v-model="server_item.username" label="Username" style="padding-top:0px;"></v-text-field>
                <v-text-field v-model="server_item.password" label="Password" style="padding-top:0px;"></v-text-field>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="server_mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected servers?</div>
              </v-flex>
              <v-btn color="success" @click="confirm_server()">Confirm</v-btn>
              <v-btn color="error" @click="server_dialog=false" style="margin-left:10px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--
    +-----------------------+
    | AUXILIARY CONNECTIONS |
    +-----------------------+
    -->
    <v-dialog v-model="auxiliary_dialog" persistent max-width="768px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ auxiliary_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="auxiliary_mode!='delete'">
                <!-- METADATA -->
                <div class="title font-weight-regular">Metadata</div>
                <v-text-field ref="field" v-model="auxiliary_item.name" label="Name" required></v-text-field>
                <!-- SQL -->
                <div class="title font-weight-regular" style="padding-top:10px;">SQL</div>
                <v-text-field v-model="auxiliary_item.hostname" label="Hostname"></v-text-field>
                <v-text-field v-model="auxiliary_item.username" label="Username" style="padding-top:0px;"></v-text-field>
                <v-text-field v-model="auxiliary_item.password" label="Password" style="padding-top:0px;"></v-text-field>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="auxiliary_mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected auxiliary connections?</div>
              </v-flex>
              <v-btn color="success" @click="confirm_auxiliary()">Confirm</v-btn>
              <v-btn color="error" @click="auxiliary_dialog=false" style="margin-left:10px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    // +--------+
    // | GROUPS |
    // +--------+
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Description', align: 'left', value: 'description' }
    ],
    items: [],
    selected: [],
    search: '',
    item: { name: '', description: '' },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialog_valid: false,

    // +--------------+
    // | ENVIRONMENTS |
    // +--------------+
    environment_headers: [{ text: 'Name', value: 'name', align: 'left', sortable: 'false' }],
    environment_items: [],
    environment_selected: [],
    environment_search: '',
    environment_item: { name: '' },
    environment_mode: '',
    environment_dialog: false,
    environment_dialog_title: '',
    environments_list: [],

    // +---------+
    // | REGIONS |
    // +---------+
    region_headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', align: 'left', value: 'environment' },
      { text: 'Cross Region', align: 'left', value: 'cross_region'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    region_items: [],
    region_selected: [],
    region_search: '',
    region_item: { name: '', environment: '', cross_region: '', hostname: '', username: '', password: '' },
    region_mode: '',
    region_dialog: false,
    region_dialog_title: '',
    regions_list: [],

    // +---------+
    // | SERVERS |
    // +---------+
    server_headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', align: 'left', value: 'environment'},
      { text: 'Region', align: 'left', value: 'region'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    server_items: [],
    server_selected: [],
    server_search: '',
    server_item: { name: '', environment: '', region: '', hostname: '', username: '', password: '' },
    server_mode: '',
    server_dialog: false,
    server_dialog_title: '',

    // +-----------------------+
    // | AUXILIARY CONNECTIONS |
    // +-----------------------+
    auxiliary_headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    auxiliary_items: [],
    auxiliary_selected: [],
    auxiliary_search: '',
    auxiliary_item: { name: '', hostname: '', username: '', password: '' },
    auxiliary_mode: '',
    auxiliary_dialog: false,
    auxiliary_dialog_title: '',

    // +-------+
    // | SLACK |
    // +-------+
    slack_webhook: '',
    slack_enabled: false,

    // +-----------+
    // | AMAZON S3 |
    // +-----------+
    s3_aws_access_key: '',
    s3_aws_secret_access_key: '',
    s3_region_name: '',
    s3_bucket_name: '',
    s3_enabled: false,

    // +-----+
    // | WEB |
    // +-----+
    web_public_url: '',

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getGroups()
  },
  methods: {
    // +--------+
    // | GROUPS |
    // +--------+
    getGroups() {
      const path = this.$store.getters.url + '/admin/groups'
      axios.get(path)
        .then((response) => {
          this.loading = false
          this.items = response.data.data
        })
        .catch((error) => {
          this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    newGroup() {
      this.mode = 'new'
      this.item = { name: '', description: '' },
      this.dialog_title = 'New Group'
      this.dialog = true
    },
    editGroup() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.dialog_title = 'Edit Group'
      this.dialog = true
    },
    deleteGroup() {
      this.mode = 'delete'
      this.dialog_title = 'Delete Group'
      this.dialog = true
    },
    submitGroup() {
      this.loading = true
      if (this.mode == 'new') this.newGroupSubmit()
      else if (this.mode == 'edit') this.editGroupSubmit()
      else if (this.mode == 'delete') this.deleteGroupSubmit()
    },
    newGroupSubmit() {
      // Ensure that fields are filled
      if (this.item.name.length == 0 || this.item.name.length == 0) {
        this.notification('Name and Description cannot be empty', 'error')
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.item.name) {
          this.notification('Group currently exists', 'error')
          return
        }
      }
      // Add item to the DB
      const path = this.$store.getters.url + '/admin/groups'
      const payload = JSON.stringify(this.item);
      axios.post(path, payload)
        .then((response) => {
          this.notification(response.data.message, 'success')
          // Add item in the data table
          this.items.push(this.item)
          this.dialog = false
          this.loading = false
        })
        .catch((error) => {
          this.notification(error.response.data.message, 'error')
          this.loading = false
          // eslint-disable-next-line
          console.error(error)
        })
    },
    editGroupSubmit() {
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['name'] == this.item.name && this.item.name != this.selected[0]['name']) {
          this.notification('This group currently exists', 'error')
          return
        }
      }
      // Add item to the DB
      const path = this.$store.getters.url + '/admin/groups'
      const payload = { current_name: this.selected[0]['name'], name: this.item.name, description: this.item.description }
      axios.put(path, payload)
        .then((response) => {
          this.notification(response.data.message, 'success')
          // Edit item in the data table
          this.items.splice(i, 1, this.item)
          this.selected[0] = this.item
          this.dialog = false
          this.loading = false
        })
        .catch((error) => {
          this.notification(error.response.data.message, 'error')
          this.loading = false
          // eslint-disable-next-line
          console.error(err)
        })
    },
    deleteGroupSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) {
        payload.push(this.selected[i]['name'])
      }
      // Delete items to the DB
      const path = this.$store.getters.url + '/admin/groups'
      axios.delete(path, { data: payload })
        .then((response) => {
          this.notification(response.data.message, 'success')
          // Delete items from the data table
          while(this.selected.length > 0) {
            var s = this.selected.pop()
            for (var i = 0; i < this.items.length; ++i) {
              if (this.items[i]['name'] == s['name']) {
                // Delete Item
                this.items.splice(i, 1)
                break
              }
            }
            this.dialog = false
            this.loading = false
          }
        })
        .catch((error) => {
          this.notification(error.response.data.message, 'error')
          this.loading = false
          // eslint-disable-next-line
          console.error(error)
        })
    },
    // +--------------+
    // | ENVIRONMENTS |
    // +--------------+
    new_environment() {
      this.environment_mode = 'new'
      this.environment_item = { name: '' }
      this.environment_dialog_title = 'New Environment'
      this.environment_dialog = true
    },
    edit_environment() {
      this.environment_mode = 'edit'
      this.environment_item = JSON.parse(JSON.stringify(this.environment_selected[0]))
      this.environment_dialog_title = 'Edit Environment'
      this.environment_dialog = true
    },
    delete_environment() {
      this.environment_mode = 'delete'
      this.environment_dialog_title = 'Delete Environment'
      this.environment_dialog = true
    },
    confirm_environment() {
      if (this.environment_mode == 'new') this.new_environment_confirm()
      else if (this.environment_mode == 'edit') this.edit_environment_confirm()
      else if (this.environment_mode == 'delete') this.delete_environment_confirm()
    },
    new_environment_confirm() {
      // Check if new item already exists
      for (var i = 0; i < this.environment_items.length; ++i) {
        if (this.environment_items[i]['name'] == this.item.name) {
          this.notification('Environment currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.environment_items.push(this.environment_item)
      this.environment_dialog = false
      this.notification('Environment added successfully', 'success')
    },
    edit_environment_confirm() {
      // Get Item Position
      for (var i = 0; i < this.environment_items.length; ++i) {
        if (this.environment_items[i]['name'] == this.environment_selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.environment_items.length; ++j) {
        if (this.environment_items[j]['name'] == this.environment_item.name && this.environment_item.name != this.environment_selected[0]['name']) {
          this.notification('Environment currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.environment_items.splice(i, 1, this.environment_item)
      this.environment_dialog = false
      this.notification('Environment edited successfully', 'success')
    },
    delete_environment_confirm() {
      while(this.environment_selected.length > 0) {
        var s = this.environment_selected.pop()
        for (var i = 0; i < this.environment_items.length; ++i) {
          if (this.environment_items[i]['name'] == s['name']) {
            // Delete Item
            this.environment_items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected environments removed successfully', 'success')
      this.environment_dialog = false
    },
    // +---------+
    // | REGIONS |
    // +---------+
    new_region() {
      this.region_mode = 'new'
      this.region_item = { name: '', environment: '', cross_region: '', hostname: '', username: '', password: '' }
      this.region_dialog_title = 'New Region'
      this.region_dialog = true
    },
    edit_region() {
      this.region_mode = 'edit'
      this.region_item = JSON.parse(JSON.stringify(this.region_selected[0]))
      this.region_dialog_title = 'Edit Region'
      this.region_dialog = true
    },
    delete_region() {
      this.region_mode = 'delete'
      this.region_dialog_title = 'Delete Region'
      this.region_dialog = true
    },
    confirm_region() {
      if (this.region_mode == 'new') this.new_region_confirm()
      else if (this.region_mode == 'edit') this.edit_region_confirm()
      else if (this.region_mode == 'delete') this.delete_region_confirm()
    },
    new_region_confirm() {
      // Check if new item already exists
      for (var i = 0; i < this.region_items.length; ++i) {
        if (this.region_items[i]['name'] == this.item.name) {
          this.notification('Region currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.region_items.push(this.region_item)
      this.region_dialog = false
      this.notification('Region added successfully', 'success')
    },
    edit_region_confirm() {
      // Get Item Position
        for (var i = 0; i < this.region_items.length; ++i) {
        if (this.region_items[i]['name'] == this.region_selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.region_items.length; ++j) {
        if (this.region_items[j]['name'] == this.region_item.name && this.region_item.name != this.region_selected[0]['name']) {
          this.notification('Region currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.region_items.splice(i, 1, this.region_item)
      this.region_dialog = false
      this.notification('Region edited successfully', 'success')
    },
    delete_region_confirm() {
      while(this.region_selected.length > 0) {
        var s = this.region_selected.pop()
        for (var i = 0; i < this.region_items.length; ++i) {
          if (this.region_items[i]['name'] == s['name']) {
            // Delete Item
            this.region_items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected regions removed successfully', 'success')
      this.region_dialog = false
    },
    // +---------+
    // | SERVERS |
    // +---------+
    new_server() {
      this.server_mode = 'new'
      this.server_item = { name: '', environment: '', region: '', hostname: '', username: '', password: '' }
      this.server_dialog_title = 'New Server'
      this.server_dialog = true
    },
    edit_server() {
      this.server_mode = 'edit'
      this.server_item = JSON.parse(JSON.stringify(this.server_selected[0]))
      this.server_dialog_title = 'Edit Server'
      this.server_dialog = true
    },
    delete_server() {
      this.server_mode = 'delete'
      this.server_dialog_title = 'Delete Server'
      this.server_dialog = true
    },
    confirm_server() {
      if (this.server_mode == 'new') this.new_server_confirm()
      else if (this.server_mode == 'edit') this.edit_server_confirm()
      else if (this.server_mode == 'delete') this.delete_server_confirm()
    },
    new_server_confirm() {
      // Check if new item already exists
      for (var i = 0; i < this.server_items.length; ++i) {
        if (this.server_items[i]['name'] == this.item.name) {
          this.notification('Server currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.server_items.push(this.server_item)
      this.server_dialog = false
      this.notification('Server added successfully', 'success')
    },
    edit_server_confirm() {
      // Get Item Position
        for (var i = 0; i < this.server_items.length; ++i) {
        if (this.server_items[i]['name'] == this.server_selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.server_items.length; ++j) {
        if (this.server_items[j]['name'] == this.server_item.name && this.server_item.name != this.server_selected[0]['name']) {
          this.notification('Server currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.server_items.splice(i, 1, this.server_item)
      this.server_dialog = false
      this.notification('Server edited successfully', 'success')
    },
    delete_server_confirm() {
      while(this.server_selected.length > 0) {
        var s = this.server_selected.pop()
        for (var i = 0; i < this.server_items.length; ++i) {
          if (this.server_items[i]['name'] == s['name']) {
            // Delete Item
            this.server_items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected servers removed successfully', 'success')
      this.server_dialog = false
    },
    // +-----------------------+
    // | AUXILIARY CONNECTIONS |
    // +-----------------------+
    new_auxiliary() {
      this.auxiliary_mode = 'new'
      this.auxiliary_item = { name: '', hostname: '', username: '', password: '' }
      this.auxiliary_dialog_title = 'New Auxiliary Connection'
      this.auxiliary_dialog = true
    },
    edit_auxiliary() {
      this.auxiliary_mode = 'edit'
      this.auxiliary_item = JSON.parse(JSON.stringify(this.auxiliary_selected[0]))
      this.auxiliary_dialog_title = 'Edit Auxiliary Connection'
      this.auxiliary_dialog = true
    },
    delete_auxiliary() {
      this.auxiliary_mode = 'delete'
      this.auxiliary_dialog_title = 'Delete Auxiliary Connection'
      this.auxiliary_dialog = true
    },
    confirm_auxiliary() {
      if (this.auxiliary_mode == 'new') this.new_auxiliary_confirm()
      else if (this.auxiliary_mode == 'edit') this.edit_auxiliary_confirm()
      else if (this.auxiliary_mode == 'delete') this.delete_auxiliary_confirm()
    },
    new_auxiliary_confirm() {
      // Check if new item already exists
      for (var i = 0; i < this.auxiliary_items.length; ++i) {
        if (this.auxiliary_items[i]['name'] == this.item.name) {
          this.notification('Auxiliary Connection currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.auxiliary_items.push(this.auxiliary_item)
      this.auxiliary_dialog = false
      this.notification('Auxiliary Connection added successfully', 'success')
    },
    edit_auxiliary_confirm() {
      // Get Item Position
        for (var i = 0; i < this.auxiliary_items.length; ++i) {
        if (this.auxiliary_items[i]['name'] == this.auxiliary_selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.auxiliary_items.length; ++j) {
        if (this.auxiliary_items[j]['name'] == this.auxiliary_item.name && this.auxiliary_item.name != this.auxiliary_selected[0]['name']) {
          this.notification('Auxiliary Connection currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.auxiliary_items.splice(i, 1, this.auxiliary_item)
      this.auxiliary_dialog = false
      this.notification('Auxiliary Connection edited successfully', 'success')
    },
    delete_auxiliary_confirm() {
      while(this.auxiliary_selected.length > 0) {
        var s = this.auxiliary_selected.pop()
        for (var i = 0; i < this.auxiliary_items.length; ++i) {
          if (this.auxiliary_items[i]['name'] == s['name']) {
            // Delete Item
            this.auxiliary_items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected auxiliary connections removed successfully', 'success')
      this.auxiliary_dialog = false
    },
    // SNACKBAR
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
  },
  watch: {
    environment_dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script> 