<template>
  <div>
    <div v-if="this.$route.params.id !== undefined">
      <router-view/>
    </div>
    <div v-else>
      <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="font-size:0.9rem!important"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-users</v-icon>GROUPS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn text @click="newGroup()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1" text @click="editGroup()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn :disabled="selected.length != 1" text @click="cloneGroup()"><v-icon small style="padding-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn :disabled="selected.length == 0" text @click="deleteGroup()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="getGroups" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="openColumnsDialog" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="search" @current-items="(items) => current = items" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="checkboxClick">
          </v-simple-checkbox>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-minus</v-icon>DELETE GROUPS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div class="subtitle-1">Are you sure you want to delete the selected groups?</div>
                <v-card style="margin-top:15px; margin-bottom:15px">
                  <v-list>
                    <v-list-item v-for="item in selected" :key="item.name" style="min-height:35px">
                      <v-list-item-content style="padding:0px">
                        <v-list-item-title>{{ item.name }}</v-list-item-title>
                      </v-list-item-content>
                    </v-list-item>
                  </v-list>
                </v-card>
                <v-checkbox v-model="dialogConfirm" label="I confirm I want to delete my Meteor Next account." style="margin-bottom:15px" hide-details>
                  <template v-slot:label>
                    <div style="margin-left:5px">
                      <div style="color:#e2e2e2">I confirm I want to delete the selected groups.</div>
                      <div class="font-weight-regular caption" style="font-size:0.85rem !important">The inventory related to the selected groups will be deleted as well.</div>
                    </div>
                  </template>
                </v-checkbox>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :disabled="!dialogConfirm" color="#00b16a" @click="deleteGroupSubmit()">Confirm</v-btn>
                  <v-btn color="#EF5354" @click="dialog=false" style="margin-left:5px">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-------------------->
    <!-- COLUMNS DIALOG -->
    <!-------------------->
    <v-dialog v-model="columnsDialog" max-width="600px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="text-subtitle-1 white--text">FILTER COLUMNS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAllColumns" text title="Select all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAllColumns" text title="Deselect all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="columnsDialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <div class="text-body-1" style="margin-bottom:10px">Select the columns to display:</div>
                  <v-checkbox v-model="columnsRaw" label="Name" value="name" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Description" value="description" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created By" value="created_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created At" value="created_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated By" value="updated_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated At" value="updated_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Users" value="users" hide-details style="margin-top:5px"></v-checkbox>
                  <v-divider style="margin-top:15px;"></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn @click="filterColumns" :loading="loading" color="#00b16a">Confirm</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="columnsDialog = false" style="margin-left:5px;">Cancel</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import moment from 'moment';

export default {
  data: () => ({
    // +--------+
    // | GROUPS |
    // +--------+
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Description', align: 'left', value: 'description' },
      { text: 'Created By', align: 'left', value: 'created_by' },
      { text: 'Created At', align: 'left', value: 'created_at' },
      { text: 'Updated By', align: 'left', value: 'updated_by' },
      { text: 'Updated At', align: 'left', value: 'updated_at' },
      { text: 'Users', align: 'left', value: 'users' }
    ],
    items: [],
    current: [],
    selected: [],
    search: '',
    item: { name: '', description: '' },
    loading: true,
    dialog: false,
    dialogConfirm: false,
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','description','created_at','updated_at','users'],
    columnsRaw: [],
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    // Get Groups
    this.getGroups()
  },
  updated() {
    // Check Notifications
    if (this.$route.params.msg) {
      this.notification(this.$route.params.msg, this.$route.params.color)
      this.selected = []
      this.getGroups()
    }
    this.$route.params.msg = null
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  methods: {
    getGroups() {
      this.loading = true
      axios.get('/admin/groups')
        .then((response) => {
          this.items = response.data.data.map(x => ({...x, created_at: this.dateFormat(x.created_at), updated_at: this.dateFormat(x.updated_at)}))
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    newGroup() {
      this.$router.push({ name:'admin.group', params: { id: null, mode: 'new' }})
    },
    editGroup() {
      this.$router.push({ name:'admin.group', params: { id: this.selected[0]['id'], mode: 'edit' }})
    },
    cloneGroup() {
      this.$router.push({ name:'admin.group', params: { id: this.selected[0]['id'], mode: 'clone' }})
    },
    deleteGroup() {
      this.dialogConfirm = false
      this.dialog = true
    },
    deleteGroupSubmit() {
      this.loading = true
      // Build payload
      const payload = { groups: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/admin/groups', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Delete items from the data table
          while(this.selected.length > 0) {
            var s = this.selected.pop()
            for (var i = 0; i < this.items.length; ++i) {
              if (this.items[i]['id'] == s['id']) {
                // Delete Item
                this.items.splice(i, 1)
                break
              }
            }
          }
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','description','created_by','created_at','updated_by','updated_at','users']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
    checkboxClick() {
      if (this.search.trim().length == 0) this.selected.length == this.items.length ? this.selected = [] : this.selected = [...this.items]
      else {
        const allSelected = this.current.every(x => this.selected.find(y => y.id == x.id))
        if (allSelected) this.selected = this.selected.filter(x => !this.current.find(y => y.id == x.id))
        else this.selected = this.selected.filter(x => !this.current.find(y => y.id == x.id)).concat(this.current)
      }
    },
  }
}
</script> 