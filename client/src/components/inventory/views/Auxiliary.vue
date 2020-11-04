<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">AUXILIARY CONNECTIONS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newAuxiliary()" class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editAuxiliary()" class="body-2"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteAuxiliary()" class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:[`item.ssh_tunnel`]="{ item }">
          <v-icon v-if="item.ssh_tunnel" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
          <v-icon v-else small color="error" style="margin-left:20px">fas fa-circle</v-icon>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-top:15px; margin-bottom:15px;">
                  <!-- METADATA -->
                  <v-text-field ref="field" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <!-- SQL -->
                  <div class="title font-weight-regular">SQL</div>
                  <v-select v-model="item.sql_engine" :items="engines_items" label="Engine" :rules="[v => !!v || '']" required v-on:change="selectEngine"></v-select>
                  <v-text-field v-model="item.sql_hostname" :rules="[v => !!v || '']" label="Hostname" style="padding-top:0px;" append-icon="cloud"></v-text-field>
                  <v-text-field v-model="item.sql_port" :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px;" append-icon="directions_boat"></v-text-field>
                  <v-text-field v-model="item.sql_username" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;" append-icon="person"></v-text-field>
                  <v-text-field v-model="item.sql_password" label="Password" style="padding-top:0px;" hide-details append-icon="lock"></v-text-field>
                  <!-- SSH -->
                  <v-switch v-model="item.ssh_tunnel" label="SSH Tunnel" color="info" hide-details style="margin-top:20px;"></v-switch>
                  <div v-if="item.ssh_tunnel" style="margin-top:15px;">
                    <div class="title font-weight-regular">SSH</div>
                    <v-text-field v-model="item.ssh_hostname" :rules="[v => !!v || '']" label="Hostname" append-icon="cloud"></v-text-field>
                    <v-text-field v-model="item.ssh_port" :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px;" append-icon="directions_boat"></v-text-field>
                    <v-text-field v-model="item.ssh_username" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;" append-icon="person"></v-text-field>
                    <v-text-field v-model="item.ssh_password" label="Password" style="padding-top:0px;" append-icon="lock"></v-text-field>
                    <v-textarea v-model="item.ssh_key" label="Private Key" rows="2" filled auto-grow style="padding-top:0px;" append-icon="vpn_key" hide-details></v-textarea>
                  </div>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected auxiliary connections?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitAuxiliary()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:5px">CANCEL</v-btn>
                  <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="testConnection()" style="float:right;">Test Connection</v-btn>
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
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Engine', align: 'left', value: 'sql_engine'},
      { text: 'Hostname', align: 'left', value: 'sql_hostname'},
      { text: 'Port', align: 'left', value: 'sql_port'},
      { text: 'Username', align: 'left', value: 'sql_username'},
      { text: 'Password', align: 'left', value: 'sql_password'},
      { text: 'SSH Tunnel', align: 'left', value: 'ssh_tunnel'}
    ],
    items: [],
    selected: [],
    search: '',
    item: { name: '', ssh_tunnel: false, ssh_hostname: '', ssh_port: 22, ssh_username: '', ssh_password: '', ssh_key: '', sql_engine: '', sql_hostname: '', sql_port: '', sql_username: '', sql_password: '' },
    mode: '',
    loading: true,
    engines_items: ['MySQL', 'PostgreSQL'],
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
      axios.get('/inventory/auxiliary')
        .then((response) => {
          this.items = response.data.data
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    selectEngine(value) {
      if (this.item['sql_port'] == '') {
        if (value == 'MySQL') this.item['sql_port'] = '3306'
        else if (value == 'PostgreSQL') this.item['sql_port'] = '5432'
      }
    },
    newAuxiliary() {
      this.mode = 'new'
      this.item = { name: '', ssh_tunnel: false, ssh_hostname: '', ssh_port: 22, ssh_username: '', ssh_password: '', ssh_key: '', sql_engine: '', sql_hostname: '', sql_port: '', sql_username: '', sql_password: '' }
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
        this.loading = false
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.item.name) {
          this.notification('This auxiliary connection currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Add item in the DB
      const payload = this.item
      axios.post('/inventory/auxiliary', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getAuxiliary()
          this.dialog = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    editAuxiliarySubmit() {
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
        if (this.items[j]['name'] == this.item.name && this.item.name != this.selected[0]['name']) {
          this.notification('This auxiliary connection currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Edit item in the DB
      const payload = this.item
      axios.put('/inventory/auxiliary', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          this.items.splice(i, 1, this.item)
          this.dialog = false
          this.selected = []
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    deleteAuxiliarySubmit() {
      // Build payload
      const payload = { auxiliary: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/inventory/auxiliary', { params: payload })
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
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
          this.dialog = false
        })
    },
    testConnection() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Test Connection
      this.notification('Testing Auxiliary Connection...', 'info', true)
      this.loading = true
      const payload = this.item
      axios.post('/inventory/auxiliary/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    notification(message, color, persistent=false) {
      this.snackbar = false
      setTimeout(() => {
        this.snackbarText = message
        this.snackbarColor = color
        this.snackbarTimeout = persistent ? Number(0) : Number(5000)
        this.snackbar = true
      }, 10)
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