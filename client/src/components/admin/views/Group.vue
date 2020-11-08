<template>
  <div>
    <v-card>
      <v-toolbar flat dense color="primary">
        <v-toolbar-title class="white--text">{{ toolbar_title }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon title="Go back" @click="goBack()" style="margin-right:-5px;"><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn>
      </v-toolbar>
      <v-card-text>
        <v-flex>
          <v-form ref="form" v-model="form_valid">
            <!-- INFO -->
            <v-text-field ref="focus" v-model="group.name" :rules="[v => !!v || '']" label="Name" required style="margin-top:0px;"></v-text-field>
            <v-text-field v-model="group.description" :rules="[v => !!v || '']" label="Description" required style="padding-top:0px; margin-top:0px;"></v-text-field>
            <v-text-field v-model="group.coins_day" label="Coins per day" :rules="[v => v == parseInt(v) && v >= 0 || '']" required style="padding-top:0px; margin-top:0px;"></v-text-field>
            <v-text-field v-model="group.coins_max" label="Maximum coins" :rules="[v => v == parseInt(v) && v >= 0 || '']" required style="margin-top:0px; padding-top:0px;"></v-text-field>

            <!-- SERVICES - BAR -->
            <div>
              <v-tabs background-color="#263238" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
                <v-tabs-slider></v-tabs-slider>
                <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-layer-group</v-icon>INVENTORY</span></v-tab>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>DEPLOYMENTS</span></v-tab>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-desktop</v-icon>MONITORING</span></v-tab>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>UTILS</span></v-tab>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>CLIENT</span></v-tab>    
                <v-divider class="mx-3" inset vertical></v-divider>
              </v-tabs>
            </div>

            <!-- INVENTORY -->
            <v-card v-show="tabs==0" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">INVENTORY</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:20px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">
                  RIGHTS
                  <v-tooltip right>
                    <template v-slot:activator="{ on }">
                      <v-icon small style="margin-left:5px; margin-bottom:2px;" v-on="on">fas fa-question-circle</v-icon>
                    </template>
                    <span><strong style="color:#2196f3; margin-right:6px;">Access Inventory:</strong>Allow users to access to the inventory.</span>
                    <br>
                    <span><strong style="color:#fa8231; margin-right:6px;">Secure Inventory:</strong>Shared resources (regions, servers, auxiliary connections) are shown without sensible data (hostname, username, password, ...).</span>
                  </v-tooltip>
                </div>
                <v-switch v-model="group.inventory_enabled" label="Access Inventory" color="info" hide-details style="margin-top:0px;"></v-switch>
                <v-switch v-model="group.inventory_secured" label="Secure Inventory" color="#fa8231" hide-details style="margin-top:20px; padding-top:0px;"></v-switch>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:15px; margin-top:15px">
                  OWNERS
                  <v-tooltip right>
                    <template v-slot:activator="{ on }">
                      <v-icon small style="margin-left:5px; margin-bottom:2px;" v-on="on">fas fa-question-circle</v-icon>
                    </template>
                    <span>Owners can mange <strong>Shared</strong> resources (environments, regions, servers, auxiliary connections)</span>
                  </v-tooltip>
                </div>
                <v-toolbar dense flat color="#2e3131" style="border-top-left-radius:5px; border-top-right-radius:5px;">
                  <v-toolbar-items class="hidden-sm-and-down" style="margin-left:-16px">
                    <v-btn text @click="newOwners()" class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                    <v-btn v-if="inventorySelected.length > 0" text @click="removeOwners()" class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                  </v-toolbar-items>
                  <v-divider class="mx-3" inset vertical></v-divider>
                  <v-text-field v-model="inventorySearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                </v-toolbar>
                <v-data-table v-model="inventorySelected" :headers="inventoryHeaders" :items="inventoryItems" :search="inventorySearch" item-key="name" class="elevation-1" no-data-text="No owners created" hide-detault-header hide-default-footer disable-pagination>
                </v-data-table>
              </v-card-text>
            </v-card>

            <!-- DEPLOYMENTS -->
            <v-card v-show="tabs==1" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">DEPLOYMENTS</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.deployments_enabled" label="Perform Deployments" color="info" style="margin-top:0px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enabled" v-model="group.deployments_basic" label="BASIC" color="#eb974e" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enabled" v-model="group.deployments_pro" label="PRO" color="rgb(235, 95, 93)" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">
                  LIMITS
                <v-tooltip right>
                  <template v-slot:activator="{ on }">
                    <v-icon small style="margin-left:5px;" v-on="on">fas fa-question-circle</v-icon>
                  </template>
                  <span>
                    <b>Execution Threads</b>: Maximum number of spawned threads per server.
                    <br>
                    <b>Execution Limit</b>: Sets the maximum scanned rows allowed.
                    <br>
                    <b>Concurrent Executions</b>: Sets the maximum concurrent executions.
                  </span>
                </v-tooltip>
                </div>
                <v-text-field v-model="group.coins_execution" label="Coins per execution" :rules="[v => v == parseInt(v) && v >= 0 || '']" required style="margin-top:25px; padding-top:0px;"></v-text-field>
                <v-text-field v-model="group.deployments_execution_threads" label="Execution Threads" :rules="[v => v == parseInt(v) && v > 0 || '']" required style="margin-top:0px; padding-top:0px;"></v-text-field>
                <v-text-field v-model="group.deployments_execution_limit" label="Execution Limit" :rules="[v => v ? v == parseInt(v) && v > 0 : true || '']" style="margin-top:0px; padding-top:0px;"></v-text-field>
                <v-text-field v-model="group.deployments_execution_concurrent" label="Concurrent Executions" :rules="[v => v ? v == parseInt(v) && v > 0 : true || '']" style="margin-top:0px; padding-top:0px;"></v-text-field>
              </v-card-text>
            </v-card>

            <!-- MONITORING -->
            <v-card v-show="tabs==2" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">MONITORING</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.monitoring_enabled" label="Access Monitoring" color="info" style="margin-top:0px;"></v-switch>
              </v-card-text>
            </v-card>

            <!-- UTILS -->
            <v-card v-show="tabs==3" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">UTILS</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.utils_enabled" label="Access Utils" color="info" style="margin-top:0px;"></v-switch>
              </v-card-text>
            </v-card>

            <!-- CLIENT -->
            <v-card v-show="tabs==4" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">CLIENT</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.client_enabled" label="Access Client" color="info" style="margin-top:0px;"></v-switch>
              </v-card-text>
            </v-card>

            <div style="margin-top:20px;">
              <v-btn color="#00b16a" @click="submitGroup()">Confirm</v-btn>
              <router-link class="nav-link" to="/admin/groups">
                <v-btn color="error" @click="dialog=false" style="margin-left:10px">Cancel</v-btn>
              </router-link>
            </div>
          </v-form>
        </v-flex>      
      </v-card-text>
    </v-card>

    <!---------------------->
    <!-- Inventory Owners -->
    <!---------------------->
    <v-dialog v-model="dialog" persistent max-width="50%">
      <v-card>
        <v-toolbar dense v-if="dialogOptions.mode != 'delete'" flat color="primary">
          <v-toolbar-title class="white--text">{{ dialogOptions.title }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <div v-if="dialogOptions.mode == 'delete'" class="text-h6" style="font-weight:400;">{{ dialogOptions.title }}</div>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text">USERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="ownersSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-list flat dense>
                      <v-list-item-group v-model="owners" multiple>
                        <v-list-item>
                          <template v-slot:default="{ active }">
                            <v-list-item-action>
                              <v-checkbox :input-value="active"></v-checkbox>
                            </v-list-item-action>
                            <v-list-item-content>
                              <v-list-item-title>username</v-list-item-title>
                              <v-list-item-subtitle>email</v-list-item-subtitle>
                            </v-list-item-content>
                          </template>
                        </v-list-item>
                      </v-list-item-group>
                    </v-list>
                  </v-card>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogOptions.button1 }}</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">{{ dialogOptions.button2 }}</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------->
    <!-- Snackbar -->
    <!-------------->
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
/* eslint-disable */
import axios from 'axios';

export default {
  data: () => ({
    // +--------+
    // | GROUPS |
    // +--------+
    group: {
      'inventory_enabled': false,
      'inventory_secured': false,
      'deployments_enabled': false,
      'deployments_basic': false,
      'deployments_pro': false,
      'coins_execution': 10,
      'deployments_execution_threads': 10,
      'deployments_execution_limit': null,
      'deployments_execution_concurrent': null,
      'monitoring_enabled': false,
      'utils_enabled': false,
      'client_enabled': false
    },
    toolbar_title: '',
    form_valid: false,
    loading: false,

    // Inventory - Owners
    inventorySearch: '',
    inventorySelected: [],
    inventoryHeaders: [],
    inventoryItems: [],
    ownersSearch: '',
    owners: [],

    // Dialog - Basic
    dialog: false,
    dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },

    // +------+
    // | TABS |
    // +------+
    tabs: null,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.init()
  },
  methods: {
    init() {
      this.group['id'] = this.$route.params.id
      if (this.group['id'] == 'new') this.toolbar_title = 'NEW GROUP'
      else {
        this.toolbar_title = 'EDIT GROUP'
        this.getGroup()
      }
    },
    // +--------+
    // | GROUPS |
    // +--------+
    getGroup() {
      axios.get('/admin/groups', { params: { groupID: this.group['id'] } })
        .then((response) => {
          if (response.data.data.length == 0) this.$router.push('/admin/groups')
          else {
            this.group = response.data.data[0]
            this.loading = false
          }
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    submitGroup() {
      this.loading = true
      if (this.group['id'] == 'new') this.newGroupSubmit()
      else this.editGroupSubmit()
    },
    newGroupSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Parse nullable values
      if (!this.group.deployments_execution_limit) this.group.deployments_execution_limit = null
      if (!this.group.deployments_execution_concurrent) this.group.deployments_execution_concurrent = null
      // Add group to the DB
      const payload = {
        group: JSON.stringify(this.group),
        environments: this.environment_items,
        regions: this.region_items,
        servers: this.server_items,
        auxiliary: this.auxiliary_items,
        slack: JSON.stringify(this.slack),        
      }
      axios.post('/admin/groups', payload)
        .then((response) => {
          this.$router.push({ name: 'admin.groups', params: { msg: response.data.message, color: '#00b16a' }})
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    editGroupSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Parse nullable values
      if (!this.group.deployments_execution_limit) this.group.deployments_execution_limit = null
      if (!this.group.deployments_execution_concurrent) this.group.deployments_execution_concurrent = null
      // Edit group to the DB
      const payload = {
        group: JSON.stringify(this.group),
        environments: this.environment_items,
        regions: this.region_items,
        servers: this.server_items,
        auxiliary: this.auxiliary_items,
        slack: JSON.stringify(this.slack),        
      }
      axios.put('/admin/groups', payload)
        .then((response) => {
          this.$router.push({ name: 'admin.groups', params: { msg: response.data.message, color: '#00b16a' }})
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    newOwners() {
      var dialogOptions = {
      'mode': 'new',
        'title': 'New owners',
        'text': '',
        'button1': 'Submit',
        'button2': 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    removeOwners() {
      var dialogOptions = {
        'mode': 'delete',
        'title': 'Remove owners',
        'text': 'Are you sure you want to remove the selected owners?',
        'button1': 'Remove',
        'button2': 'Cancel'
      }
      this.showDialog(dialogOptions)
    },
    showDialog(options) {
      this.dialogOptions = options
      this.dialog = true
    },
    dialogSubmit() {

    },
    goBack() {
      this.$router.go(-1)
    },
    // SNACKBAR
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
        if (typeof this.$refs.focus !== 'undefined') this.$refs.focus.focus()
      })
    }
  }
}
</script>