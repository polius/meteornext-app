<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">AUXILIARY CONNECTIONS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newAuxiliary()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editAuxiliary()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteAuxiliary()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:no-results>
          <v-alert :value="true" color="error" icon="warning" style="margin-top:15px;">
            Your search for "{{ search }}" found no results.
          </v-alert>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="mode!='delete'">
                <v-form ref="form" v-model="dialog_valid">
                  <!-- METADATA -->
                  <div class="title font-weight-regular">Metadata</div>
                  <v-text-field ref="field" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <!-- SQL -->
                  <div class="title font-weight-regular">SQL</div>
                  <v-text-field v-model="item.hostname" :rules="[v => !!v || '']" label="Hostname"></v-text-field>
                  <v-text-field v-model="item.username" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.password" :rules="[v => !!v || '']" label="Password" style="padding-top:0px;"></v-text-field>
                </v-form>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected auxiliary connections?</div>
              </v-flex>
              <v-btn :loading="loading" color="success" @click="submitAuxiliary()">Confirm</v-btn>
              <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:10px">Cancel</v-btn>
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
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    items: [],
    selected: [],
    search: '',
    item: { name: '', hostname: '', username: '', password: '' },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getAuxiliary()
  },
  methods: {
    getAuxiliary() {
      const path = this.$store.getters.url + '/deployments/auxiliary'
      axios.get(path)
        .then((response) => {
          this.items = response.data.data
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    newAuxiliary() {
      this.mode = 'new'
      this.item = { name: '', hostname: '', username: '', password: '' }
      this.dialog_title = 'New Auxiliary Connection'
      this.dialog = true
    },
    editAuxiliary() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.dialog_title = 'Edit Auxiliary Connection'
      this.dialog = true
    },
    deleteAuxiliary() {
      this.mode = 'delete'
      this.dialog_title = 'Delete Auxiliary Connection'
      this.dialog = true
    },
    submitAuxiliary() {
      this.loading = true
      if (this.mode == 'new') this.newAuxiliarySubmit()
      else if (this.mode == 'edit') this.editAuxiliarySubmit()
      else if (this.mode == 'delete') this.deleteAuxiliarySubmit()
    },
    newAuxiliarySubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.item.name) {
          this.notification('This auxiliary connection currently exists', 'error')
          return
        }
      }
      // Add item in the DB
      const path = this.$store.getters.url + '/deployments/auxiliary'
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
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          this.notification(error.response.data.message, 'error')
          this.loading = false
          // eslint-disable-next-line
          console.error(error)
        })
    },
    editAuxiliarySubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['name'] == this.item.name && this.item.name != this.selected[0]['name']) {
          this.notification('This auxiliary connection currently exists', 'error')
          return
        }
      }
      // Edit item in the DB
      const path = this.$store.getters.url + '/deployments/auxiliary'
      const payload = { 
        current_name: this.selected[0]['name'], 
        name: this.item.name,
        hostname: this.item.hostname,
        username: this.item.username,
        password: this.item.password
      }
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
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          this.loading = false
          // eslint-disable-next-line
          console.error(error)
        })
    },
    deleteAuxiliarySubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) {
        payload.push({ environment: this.selected[i]['environment'], region: this.selected[i]['region'], name: this.selected[i]['name'] })
      }
      // Delete items to the DB
      const path = this.$store.getters.url + '/deployments/auxiliary'
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
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          this.loading = false
          // eslint-disable-next-line
          console.error(error)
        })
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