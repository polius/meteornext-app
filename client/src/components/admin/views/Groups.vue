<template>
  <div>
    <div v-if="this.$route.params.id !== undefined">
      <router-view/>
    </div>
    <div v-else>
      <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">GROUPS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newGroup()" class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="cloneGroup()" class="body-2"><v-icon small style="padding-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editGroup()" class="body-2"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteGroup()" class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1" style="padding-top:3px;"></v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Delete Group</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div style="padding-top:10px; padding-bottom:10px" class="subtitle-1">Are you sure you want to delete the selected groups?</div>
                <v-alert type="error" dense>The inventory related to the selected groups will be deleted as well.</v-alert>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn color="#00b16a" @click="deleteGroupSubmit()">Confirm</v-btn>
                  <v-btn color="error" @click="dialog=false" style="margin-left:10px">Cancel</v-btn>
                </div>
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
      { text: 'Created', align: 'left', value: 'created_at' },
      { text: 'Updated', align: 'left', value: 'updated_at' },
      { text: 'Users', align: 'left', value: 'users' }
    ],
    items: [],
    selected: [],
    search: '',
    item: { name: '', description: '' },
    loading: true,
    dialog: false,
  
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
  methods: {
    // +--------+
    // | GROUPS |
    // +--------+
    getGroups() {
      axios.get('/admin/groups')
        .then((response) => {
          this.items = response.data.data.map(x => ({...x, created_at: this.dateFormat(x.created_at), updated_at: this.dateFormat(x.updated_at)}))
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
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
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    // SNACKBAR
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script> 