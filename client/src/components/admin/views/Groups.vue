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
          <v-toolbar-title class="white--text">Delete Group</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 style="padding-bottom:10px">
                <div class="subtitle-1">Are you sure you want to delete the selected groups?</div>
              </v-flex>
              <v-btn color="success" @click="deleteGroupSubmit()">Confirm</v-btn>
              <v-btn color="error" @click="dialog=false" style="margin-left:10px">Cancel</v-btn>
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
    loading: true,
    dialog: false,
  
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
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // eslint-disable-next-line
          console.error(error)
        })
    },
    newGroup() {
      this.$router.push({ name: 'admin.groups.view', params: { groupID: '' } })
    },
    editGroup() {
      this.$router.push({ name: 'admin.groups.view', params: { groupID: this.selected[0]['id'] } })
    },
    deleteGroup() {
      this.dialog = true
    },
    deleteGroupSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) {
        payload.push(this.selected[i]['id'])
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
              if (this.items[i]['id'] == s['id']) {
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
    // SNACKBAR
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
  }
}
</script> 