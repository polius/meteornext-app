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
        <template v-slot:item.created_at="props">
          <span>{{ dateFormat(props.item.created_at) }}</span>
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
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div style="padding-top:10px; padding-bottom:10px" class="subtitle-1">Are you sure you want to delete the selected groups?</div>
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

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
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
      { text: 'Created', align: 'left', value: 'created_at' }
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
  mounted() {
    // Check Notification
    setTimeout(this.checkNotifications, 300)
  },
  methods: {
    // +--------+
    // | GROUPS |
    // +--------+
    getGroups() {
      axios.get('/admin/groups')
        .then((response) => {
          this.loading = false
          this.items = response.data.data
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
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
      axios.delete('/admin/groups', { data: payload })
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
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
          this.dialog = false
        })
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format('ddd, DD MMM YYYY HH:mm:ss')
      return date
    },
    // SNACKBAR
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
    checkNotifications() {
      if (this.$route.params.msg) this.notification(this.$route.params.msg, this.$route.params.color)
    }
  }
}
</script> 