<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">RELEASES</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newRelease()"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1" text @click="editRelease()"><v-icon small style="margin-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn :disabled="selected.length == 0" text @click="deleteRelease()"><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="selected.length == items.length ? selected = [] : selected = JSON.parse(JSON.stringify(items))">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.active`]="{ item }">
          <v-btn icon small @click="changeActive(item)">
            <v-icon v-if="item.active" title="Active" color="#00b16a" small>fas fa-circle</v-icon>
            <v-icon v-else title="Inactive" color="#EF5354" small>fas fa-circle</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{mode == 'new' ? 'fas fa-plus' : mode == 'edit' ? 'fas fa-feather-alt' : 'fas fa-minus'}}</v-icon>{{ dialogTitle }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <v-alert colored-border elevation="2">
                    <v-icon color="primary" style="margin-right:10px; font-size:20px"> fas fa-info-circle</v-icon>
                    Deployments associated with active Releases will be visible in the Deployments section.</v-alert>
                  <v-text-field v-if="mode!='delete'" ref="field" @keypress.enter.native.prevent="submitRelease()" v-model="name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-checkbox v-if="mode!='delete'" v-model="active" label="Active" hide-details color="primary" style="margin-top:0px; margin-bottom:20px;"></v-checkbox>
                  <div style="padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected releases?</div>
                  <v-divider></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn :loading="loading" color="#00b16a" @click="submitRelease()">CONFIRM</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog=false" style="margin-left:5px;">CANCEL</v-btn>
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
</template>

<script>
import moment from 'moment';
import axios from 'axios';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Active', align: 'left', value: 'active' },
      { text: 'Created', align: 'left', value: 'created_at' },
      { text: 'Updated', align: 'left', value: 'updated_at' }
    ],
    items: [],
    selected: [],
    search: '',
    loading: true,
    mode: '',

    // Item
    name: '',
    active: true,

    // Dialog
    dialog: false,
    dialogTitle: '',

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getReleases()
  },
  methods: {
    getReleases() {
      axios.get('/deployments/releases')
        .then((res) => {
          this.items = []
          this.$nextTick(() => {
            this.items = res.data.data.map(x => ({...x, created_at: this.dateFormat(x.created_at), updated_at: this.dateFormat(x.updated_at)}))
          })
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    newRelease() {
      this.mode = 'new'
      this.name = ''
      this.active = true
      this.dialogTitle = 'NEW RELEASE'
      this.dialog = true
    },
    editRelease() {
      this.mode = 'edit'
      this.name = this.selected[0]['name']
      this.active = this.selected[0]['active']
      this.dialogTitle = 'EDIT RELEASE'
      this.dialog = true
    },
    deleteRelease() {
      this.mode = 'delete'
      this.dialogTitle = 'DELETE RELEASE'
      this.dialog = true
    },
    submitRelease() {
      this.loading = true
      if (this.mode == 'new') this.newReleaseSubmit()
      else if (this.mode == 'edit') this.editReleaseSubmit()
      else if (this.mode == 'delete') this.deleteReleaseSubmit()
    },
    newReleaseSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.name) {
          this.notification('This release currently exists', '#EF5354')
          this.loading = false
          return
        }
      }
      // Add item in the DB
      const payload = { name: this.name, active: this.active }
      axios.post('/deployments/releases', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getReleases()
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    editReleaseSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['name'] == this.name && this.name != this.selected[0]['name']) {
          this.notification('This release currently exists', '#EF5354')
          this.loading = false
          return
        }
      }
      // Edit item in the DB
      const payload = { id: this.selected[0]['id'], name: this.name, active: this.active }
      axios.put('/deployments/releases', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getReleases()
          this.dialog = false
          this.selected = []
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteReleaseSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) payload.push(this.selected[i]['id'])
      // Delete items to the DB
      axios.delete('/deployments/releases', { data: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
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
          }
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    changeActive(item) {
      // Add item in the DB
      const payload = { id: item.id, active: !item.active }
      axios.put('/deployments/releases/active', payload)
        .then(() => {
          this.getReleases()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script>