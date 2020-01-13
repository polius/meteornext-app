<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <div class="title font-weight-regular" style="margin-left:10px; margin-top:5px;">INBENTA</div>
          <v-form ref="form" style="padding:10px;">
            <v-text-field v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
            <v-select :loading="loading" v-model="release" :items="release_items" label="Release" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>

            <!-- EXECUTION -->
            <v-select :loading="loading" v-model="environment" :items="environment_items" label="Environment" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
            <v-select :loading="loading" v-model="products" :items="Object.keys(product_items)" label="Products" multiple :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
            <v-select :loading="loading" v-model="schema" :items="schema_items" label="Schema" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
            <v-text-field v-model="databases" label="Databases" hint="(Optional) Separated by commas. Wildcards allowed: % _" style="padding-top:0px;"></v-text-field>

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
              <v-data-table v-model="query_selected" :headers="query_headers" :items="query_items" item-key="query" show-select :hide-default-footer="query_items.length < 11" class="elevation-1">
              </v-data-table>
            </v-card>

            <!-- PARAMETERS -->
            <div class="subtitle-1 font-weight-regular">METHOD</div>
            <v-radio-group v-model="method" style="margin-top:10px;">
              <v-radio value="validate" color="success">
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

            <v-switch :disabled="loading" v-model="schedule_enabled" @change="schedule_change()" label="Sheduled" color="info" hide-details style="margin-top:-10px;"></v-switch>
            <v-text-field v-if="schedule_enabled" solo v-model="schedule_datetime" @click="schedule_change()" title="Click to edit the schedule datetime" hide-details readonly style="margin-top:10px; margin-bottom:10px;"></v-text-field>

            <v-checkbox v-else v-model="start_execution" label="Start execution" color="primary" hide-details style="margin-top:15px; margin-bottom:20px;"></v-checkbox>
            <v-divider></v-divider>

            <div style="margin-top:20px;">
              <v-btn :loading="loading" color="success" @click="submitDeploy()">CREATE DEPLOY</v-btn>
              <router-link to="/deployments"><v-btn :disabled="loading" color="error" style="margin-left:10px;">CANCEL</v-btn></router-link>
            </div>
          </v-form>
        </v-flex>
      </v-layout>
    </v-container>

    <v-dialog v-model="scheduleDialog" persistent width="290px">
      <v-date-picker v-if="schedule_mode=='date'" v-model="schedule_date" color="info" scrollable>
        <v-spacer></v-spacer>
        <v-btn text color="error" @click="schedule_close()">Cancel</v-btn>
        <v-btn text color="success" @click="schedule_submit()">Confirm</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="schedule_mode=='time'" v-model="schedule_time" color="info" format="24hr" scrollable>
        <v-spacer></v-spacer>
        <v-btn text color="error" @click="schedule_close()">Cancel</v-btn>
        <v-btn text color="success" @click="schedule_submit()">Confirm</v-btn>
      </v-time-picker>
    </v-dialog>

    <v-dialog v-model="queryDialog" persistent max-width="600px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ queryDialogTitle }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="query_form" v-if="query_mode!='delete'" style="margin-top:15px; margin-bottom:20px;">
                  <v-textarea ref="field" rows="1" filled auto-grow hide-details v-model="query_item.query" label="Query" :rules="[v => !!v || '']" required></v-textarea>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="query_mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected queries?</div>
                <v-divider v-if="query_mode=='delete'"></v-divider>
                <div style="margin-top:20px;">
                  <v-btn color="success" @click="actionConfirm()">Confirm</v-btn>
                  <v-btn color="error" @click="queryDialog=false" style="margin-left:5px">Cancel</v-btn>
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
import axios from 'axios'
import moment from 'moment'

export default {
  data() {
    return {
      name: '',
      databases: '',

      // Environment
      environment: '',
      environment_items: [],

      // Products
      product_items: {'Chatbot': 'chatbot', 'KM': 'km', 'Search': 'search', 'Ticketing': 'ticketing', 'Legacy': 'no-product'},
      products: [],
      
      // Schema
      schema_items: ['logs_cmpl', 'tmpl_edit', 'tickets'],
      schema: [],

      // Query
      query_headers: [{ text: 'Query', value: 'query' }],
      query_items: [],
      query_item: { query: '' },
      query_selected: [],
      query_mode: '', // new, edit, delete

      // Parameters
      release: '',
      release_items: [],
      method: 'validate',
      start_execution: false,

      // Schedule
      scheduleDialog: false,
      schedule_enabled: false,
      schedule_mode: 'date',
      schedule_date: '',
      schedule_time: '',
      schedule_datetime: '',

      // Query Dialog
      queryDialog: false,
      queryDialogTitle: '',

      // Loading Fields
      loading: false,
      
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  created() {
    this.getReleases()
    this.getEnvironments()
  },
  methods: {
    getReleases() {
      axios.get('/deployments/releases/active')
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.release_items.push(response.data.data[i]['name'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    getEnvironments() {
      axios.get('/deployments/environments')
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.environment_items.push(response.data.data[i]['name'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    schedule_close() {
      this.scheduleDialog = false
      if (this.schedule_mode == 'date') this.schedule_date = this.schedule_datetime.substring(0,10)
      else if (this.schedule_mode == 'time') this.schedule_time = this.schedule_datetime.substring(11,16)
      this.schedule_mode = 'date'
    },
    schedule_change() {
      if (this.schedule_enabled) {
        if (this.schedule_datetime == '') {
          const date = moment()
          this.schedule_date = date.format("YYYY-MM-DD")
          this.schedule_time = date.format("HH:mm")
          this.schedule_datetime = date.format("YYYY-MM-DD HH:mm")
        }
        this.scheduleDialog = true
      }
      else this.scheduleDialog = false
    },
    schedule_submit() {
      this.schedule_datetime = this.schedule_date + ' ' + this.schedule_time

      if (this.schedule_mode == 'date') {
        this.schedule_mode = 'time'
      }
      else if (this.schedule_mode == 'time') {
        this.scheduleDialog = false
        this.schedule_mode = 'date'
      }
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
      this.queryDialogText = 'Are you sure you want to delete the selected queries?'
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
      this.query_selected = []
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
      this.query_selected = []
      this.queryDialog = false
      this.notification('Query edited successfully', 'success')
    },
    deleteQueryConfirm() {
      while(this.query_selected.length > 0) {
        var s = this.query_selected.pop()
        for (var i = 0; i < this.query_items.length; ++i) {
          if (this.query_items[i]['query'] == s['query']) {
            // Delete Item
            this.query_items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected queries removed successfully', 'success')
      this.queryDialog = false
    },
    submitDeploy() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', 'error')
        return
      }
      if (this.query_items.length == 0) {
        this.notification('Please enter a query to deploy', 'error')
        return
      }
      this.loading = true

      // Build products list
      var products_parsed = []
      for (var i = 0; i < this.products.length; ++i) products_parsed.push(this.product_items[this.products[i]])

      // Build parameters
      const payload = {
        name: this.name,
        release: this.release,
        environment: this.environment,
        products: products_parsed,
        schema: this.schema,
        databases: this.databases,
        queries: JSON.stringify(this.query_items),
        method: this.method.toUpperCase(),
        start_execution: this.start_execution
      }
      // Add deployment to the DB
      axios.post('/deployments/inbenta', payload)
        .then((response) => {
          const data = response.data.data
          this.notification(response.data.message, 'success')
          // Refresh user coins
          this.$store.dispatch('coins', data['coins'])
          // Redirect page
          this.$router.push({ name:'deployment', params: { id: 'I' + data['execution_id'], admin: false }})
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
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