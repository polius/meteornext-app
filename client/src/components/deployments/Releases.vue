<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">RELEASES</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn v-if="selected.length == 0" text @click='newRelease()' class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editRelease()" class="body-2"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteRelease()" class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;">
        <template v-slot:item.active="props">
          <v-btn icon small @click="changeActive(props.item)">
            <v-icon v-if="props.item.active" small title="Active" color="#00b16a">fas fa-circle</v-icon>
            <v-icon v-else small title="Inactive" color="error">fas fa-circle</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialogTitle }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <v-text-field v-if="mode!='delete'" ref="field" @keypress.enter.native.prevent="submitRelease()" v-model="name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-switch v-if="mode!='delete'" v-model="active" :label="`${active ? 'Active' : 'Inactive'}`" hide-details color="info" style="margin-top:0px; margin-bottom:20px;"></v-switch>
                  <div style="padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected releases?</div>
                  <v-divider></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn :loading="loading" color="#00b16a" @click="submitRelease()">CONFIRM</v-btn>
                    <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:5px;">CANCEL</v-btn>
                  </div>
                </v-form>
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

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Active', align: 'left', value: 'active' }
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
          this.items = res.data.data
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        });
    },
    newRelease() {
      this.mode = 'new'
      this.name = ''
      this.active = true
      this.dialogTitle = 'New Release'
      this.dialog = true
    },
    editRelease() {
      this.mode = 'edit'
      this.name = this.selected[0]['name']
      this.active = this.selected[0]['active']
      this.dialogTitle = 'Edit Release'
      this.dialog = true
    },
    deleteRelease() {
      this.mode = 'delete'
      this.dialogTitle = 'Delete Release'
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
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.name) {
          this.notification('This release currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Add item in the DB
      const payload = JSON.stringify({ name: this.name, active: this.active })
      axios.post('/deployments/releases', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getReleases()
          this.dialog = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    editReleaseSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
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
          this.notification('This release currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Edit item in the DB
      const item = { id: this.selected[0]['id'], name: this.name, active: this.active }
      const payload = JSON.stringify(item)
      axios.put('/deployments/releases', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          this.items.splice(i, 1, item)
          this.dialog = false
          this.selected = []
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
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
    changeActive(item) {
      // Add item in the DB
      const payload = JSON.stringify({ id: item.id, active: !item.active })
      axios.put('/deployments/releases/active', payload)
        .then(() => {
          this.getReleases()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
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