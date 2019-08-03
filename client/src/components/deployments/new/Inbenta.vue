<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <v-form style="padding:10px;">
            <!-- METADATA -->
            <div class="title font-weight-regular">Metadata</div>
            <v-text-field v-model="name" label="Name" hint="Example: Release v1.0.0" required></v-text-field>

            <!-- EXECUTION -->
            <div class="title font-weight-regular">Execution</div>
            <v-select v-model="product" :items="product_items" label="Product" required></v-select>
            <v-text-field v-model="databases" label="Databases" hint="Optional" required style="padding-top:0px;"></v-text-field>

            <v-card style="margin-bottom:10px;">
              <v-toolbar flat dense style="margin-top:5px;">
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
                <template v-slot:items="props">
                  <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
                  <td>{{ props.item.query }}</td>
                </template>
              </v-data-table>
            </v-card>

            <!-- PARAMETERS -->
            <div class="title font-weight-regular" style="margin-top:20px;">Parameters</div>

            <v-select v-model="environment" :items="environment_items" label="Environment" required></v-select>
            <v-radio-group v-model="execution_mode" style="margin-top:0px;">
              <template v-slot:label>
                <div>Select the <strong>Execution Mode</strong>:</div>
              </template>
              <v-radio value="validation" color="success">
                <template v-slot:label>
                  <div class="success--text">Validation</div>
                </template>
              </v-radio>
              <v-radio value="test" color="orange">
                <template v-slot:label>
                  <div class="orange--text">Test Execution</div>
                </template>
              </v-radio>
              <v-radio value="deploy" color="red">
                <template v-slot:label>
                  <div class="red--text">Deployment</div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-radio-group v-model="execution_method" style="margin-top:0px; padding-top:0px;">
              <template v-slot:label>
                <div>Select the <strong>Execution Method</strong>:</div>
              </template>
              <v-radio value="parallel">
                <template v-slot:label>
                  <div>Parallel</div>
                </template>
              </v-radio>
              <v-radio value="sequential">
                <template v-slot:label>
                  <div>Sequential</div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-text-field v-if="execution_method=='parallel'" v-model="threads" label="Threads" style="margin-top:0px; padding-top:5px; margin-bottom:5px;"></v-text-field>

            <v-btn color="success">Deploy</v-btn>
            <router-link to="/deployments"><v-btn color="error" style="margin-left:10px;">Cancel</v-btn></router-link>

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
                <v-textarea ref="field" rows="1" filled auto-grow v-model="query_item.query" label="Query" required></v-textarea>
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
export default {
  data() {
    return {
      // Metadata
      name: '',

      // Execution
      product: '',
      product_items: [],
      databases: '',
      query_headers: [{ text: 'Query', value: 'query' }],
      query_items: [],
      query_item: { query: '' },
      query_selected: [],
      query_mode: '', // new, edit, delete

      // Parameters
      environment: '',
      environment_items: [],
      execution_mode: '',
      execution_method: 'parallel',
      threads: '10',

      // Query Dialog
      queryDialog: false,
      queryDialogTitle: '',
      
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
      this.queryDialogText = 'Are you sure you want to delete the selected environments?'
      this.queryDialog = true
    },
    actionConfirm() {
      if (this.query_mode == 'new') this.newQueryConfirm()
      else if (this.query_mode == 'edit') this.editQueryConfirm()
      else if (this.query_mode == 'delete') this.deleteQueryConfirm()
    },
    newQueryConfirm() {
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
      })
    }
  }
}
</script>