<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <div class="title font-weight-regular" style="margin-left:10px; margin-top:5px;">INBENTA</div>
          <v-form ref="form" style="padding:10px;">
            <v-text-field v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
            <v-select :loading="loading" v-model="products" :items="product_items" label="Products" multiple :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
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
              <v-data-table v-model="query_selected" :headers="query_headers" :items="query_items" item-key="query" show-select hide-default-footer class="elevation-1">
              </v-data-table>
            </v-card>

            <v-divider></v-divider>

            <div style="margin-top:20px;">
              <v-btn :loading="loading" color="success" @click="submitDeploy()">START EXECUTION</v-btn>
              <router-link to="/deployments"><v-btn :disabled="loading" color="error" style="margin-left:10px;">CANCEL</v-btn></router-link>
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
                  <v-btn color="error" @click="queryDialog=false" style="margin-left:10px">Cancel</v-btn>
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

export default {
  data() {
    return {
      name: '',
      databases: '',

      // Products
      product_items: ['Chatbot','KM','Search','Ticketing','Legacy'],
      products: [],

      // Query
      query_headers: [{ text: 'Query', value: 'query' }],
      query_items: [],
      query_item: { query: '' },
      query_selected: [],
      query_mode: '', // new, edit, delete

      // Parameters
      start_execution: false,

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
  methods: {
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
      // Build parameters
      const path = this.$store.getters.url + '/deployments/inbenta'
      const payload = {
        name: this.name,
        products: this.products,
        databases: this.databases,
        queries: JSON.stringify(this.query_items),
        start_execution: this.start_execution
      }
      // Add deployment to the DB
      axios.post(path, payload)
        .then((response) => {
          const data = response.data.data
          this.notification(response.data.message, 'success')
          // Refresh user coins
          this.$store.dispatch('coins', data['coins'])
          // Redirect page
          this.$router.push({ name:'deployments.information', params: { executionID: data['execution_id'], deploymentMode: 'INBENTA' }})
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
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