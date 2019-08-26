<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <v-form ref="form" style="padding:10px;">
            <v-text-field v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
            <v-select :loading="loading" v-model="environment" :items="environment_items" label="Environment" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
            <v-text-field v-model="databases" label="Databases" hint="Separated by commas. Wildcards: %, _" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>

            <v-card style="margin-bottom:20px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:5px;">
                <v-toolbar-title class="white--text">Queries</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                  <v-btn text @click='newQuery()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                  <v-btn v-if="query_selected.length == 1" text @click="editQuery()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                  <v-btn v-if="query_selected.length > 0" text @click='deleteQuery()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                </v-toolbar-items>
              </v-toolbar>
              <v-divider></v-divider>
              <v-data-table v-model="query_selected" :headers="query_headers" :items="query_items" item-key="query" hide-default-header hide-default-footer show-select class="elevation-1">
              </v-data-table>
            </v-card>

            <!-- PARAMETERS -->
            <div class="subtitle-1 font-weight-regular">MODE</div>
            <v-radio-group v-model="execution_mode" style="margin-top:10px;">
              <v-radio value="validation" color="success">
                <template v-slot:label>
                  <div class="success--text">VALIDATE</div>
                </template>
              </v-radio>
              <v-radio value="test" color="orange">
                <template v-slot:label>
                  <div class="orange--text">TEST</div>
                </template>
              </v-radio>
              <v-radio value="deploy" color="red">
                <template v-slot:label>
                  <div class="red--text">DEPLOY</div>
                </template>
              </v-radio>
            </v-radio-group>

            <div class="subtitle-1 font-weight-regular" style="margin-top:-5px;">EXECUTION</div>
            <v-radio-group v-model="execution_method" style="margin-top:10px;">
              <v-radio color="primary" value="sequential">
                <template v-slot:label>
                  <div>Sequential</div>
                </template>
              </v-radio>
              <v-radio color="primary" value="parallel">
                <template v-slot:label>
                  <div>Parallel</div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-text-field v-if="execution_method=='parallel'" v-model="threads" label="Threads" :rules="[v => !!v || '']" required style="margin-top:0px; padding-top:0px;"></v-text-field>
            <v-checkbox v-model="start_execution" label="Start execution" color="primary" hide-details style="margin-top:-10px; margin-bottom:20px;"></v-checkbox>

            <v-divider></v-divider>

            <div style="margin-top:20px;">
              <v-btn color="success" @click="deploy()">CREATE DEPLOY</v-btn>
              <router-link to="/deployments"><v-btn color="error" style="margin-left:10px;">CANCEL</v-btn></router-link>
            </div>
          </v-form>
        </v-flex>
      </v-layout>
    </v-container>

    <v-dialog v-model="queryDialog" persistent max-width="600px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ queryDialogTitle }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="query_mode!='delete'">
                <v-form ref="query_form">
                  <v-textarea ref="field" rows="1" filled auto-grow v-model="query_item.query" label="Query" :rules="[v => !!v || '']" required></v-textarea>
                </v-form>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="query_mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected queries?</div>
              </v-flex>
              <v-btn color="success" @click="actionConfirm()">Confirm</v-btn>
              <v-btn color="error" @click="queryDialog=false" style="margin-left:10px">Cancel</v-btn>
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
import axios from 'axios'

export default {
  data() {
    return {
      name: '',
      databases: '',

      // Query
      query_headers: [{ text: 'Query', value: 'query' }],
      query_items: [],
      query_item: { query: '' },
      query_selected: [],
      query_mode: '', // new, edit, delete

      // Parameters
      environment: '',
      environment_items: [],
      execution_mode: 'validation',
      execution_method: 'sequential',
      threads: '10',
      start_execution: true,

      // Query Dialog
      queryDialog: false,
      queryDialogTitle: '',

      // Loading Fields
      loading: true,
      
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  created() {
    this.getEnvironments()
  },
  methods: {
    getEnvironments() {
      const path = this.$store.getters.url + '/deployments/environments'
      axios.get(path)
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.environment_items.push(response.data.data[i]['name'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    newQuery() {
      this.query_mode = 'new'
      this.query_item = { query: '' }
      this.queryDialogTitle = 'New Query'
      this.queryDialog = true
    },
    editQuery () {
      this.query_mode = 'edit'
      this.query_item = { query: this.query_selected[0]['query'] }
      this.queryDialogTitle = 'Edit Query'
      this.queryDialog = true
    },
    deleteQuery() {
      this.query_mode = 'delete'
      this.queryDialogTitle = 'Delete Query'
      this.queryDialogText = 'Are you sure you want to delete the selected environments?'
      this.queryDialog = true
    },
    actionConfirm() {
      if (this.query_mode == 'new') this.newQueryConfirm()
      else if (this.query_mode == 'edit') this.editQueryConfirm()
      else if (this.query_mode == 'delete') this.deleteQueryConfirm()
    },
    newQueryConfirm() {
      // Check if all fields are filled
      if (!this.$refs.query_form.validate()) {
        this.notification('Please fill the required fields', 'error')
        this.loading = false
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.query_items.length; ++i) {
        if (this.query_items[i]['query'] == this.query_item.query) {
          this.notification('Query currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.query_items.push(this.query_item)
      this.queryDialog = false
      this.notification('Query added successfully', 'success')
    },
    editQueryConfirm() {
      // Get Item Position
      for (var i = 0; i < this.query_items.length; ++i) {
        if (this.query_items[i]['query'] == this.query_selected[0]['query']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.query_items.length; ++j) {
        if (this.query_items[j]['query'] == this.query_item.query && this.query_item.query != this.query_selected[0]['query']) {
          this.notification('Query currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.query_items.splice(i, 1, this.query_item)
      this.queryDialog = false
      this.notification('Query edited successfully', 'success')
    },
    deleteQueryConfirm() {
      while(this.query_selected.length > 0) {
        var s = this.query_selected.pop()
        for (var i = 0; i < this.query_items.length; ++i) {
          if (this.query_items[i]['name'] == s['name']) {
            // Delete Item
            this.query_items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected queries removed successfully', 'success')
      this.queryDialog = false
    },
    deploy() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', 'error')
        this.loading = false
        return
      }
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    queryDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
        if (typeof this.$refs.query_form !== 'undefined') this.$refs.query_form.resetValidation()
      })
    }
  }
}
</script>