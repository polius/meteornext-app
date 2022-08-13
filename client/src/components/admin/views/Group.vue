<template>
  <div>
    <v-card>
      <v-toolbar flat dense color="primary">
        <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ toolbar_title }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="goBack()"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-card-text>
        <v-flex>
          <v-form ref="form" v-model="form_valid">
            <v-alert v-if="mode == 'clone'" dense color="#fb8c00"><v-icon style="font-size:16px; margin-bottom:2px; margin-right:10px">fas fa-exclamation-triangle</v-icon>The shared inventory (Servers, Regions, Environments, Auxiliary connections) related to this group will be cloned as well.</v-alert>
            <!-- INFO -->
            <v-text-field :disabled="loading" v-model="group.name" :rules="[v => !!v || '']" label="Name" required style="margin-top:0px;" autofocus></v-text-field>
            <v-text-field :disabled="loading" v-model="group.description" :rules="[v => !!v || '']" label="Description" required style="padding-top:0px; margin-top:0px;"></v-text-field>
            <v-text-field :disabled="loading" v-model="group.coins_day" label="Coins per day" :rules="[v => v == parseInt(v) && v >= 0 || '']" required style="padding-top:0px; margin-top:0px;"></v-text-field>
            <v-text-field :disabled="loading" v-model="group.coins_max" label="Maximum coins" :rules="[v => v == parseInt(v) && v >= 0 || '']" required style="margin-top:0px; padding-top:0px;"></v-text-field>

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
                <v-toolbar-title class="white--text subtitle-1">INVENTORY</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:20px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch :disabled="loading" v-model="group.inventory_enabled" label="Access Inventory" color="info" style="margin-top:0px" hide-details></v-switch>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:15px; margin-top:15px">
                  OWNERS
                  <v-tooltip right>
                    <template v-slot:activator="{ on }">
                      <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                    </template>
                    <span>Owners can manage <strong>Shared</strong> resources (Servers, Regions, Environments, Auxiliary Connections, Cloud Keys).</span>
                  </v-tooltip>
                </div>
                <v-toolbar dense flat color="#2e3131" style="border-top-left-radius:5px; border-top-right-radius:5px;">
                  <v-toolbar-items style="margin-left:-16px">
                    <v-btn :disabled="loading || mode == 'clone'" text @click="newOwners()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                    <v-btn :disabled="loading || ownersSelected.length == 0" text @click="removeOwners()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                  </v-toolbar-items>
                  <v-divider class="mx-3" inset vertical></v-divider>
                  <v-text-field :disabled="mode == 'clone'" v-model="ownersSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                </v-toolbar>
                <v-data-table v-model="ownersSelected" :headers="ownersHeaders" :items="ownersItems" :search="ownersSearch" item-key="username" class="elevation-1" no-data-text="No owners created" hide-detault-header hide-default-footer show-select disable-pagination mobile-breakpoint="0">
                  <template v-ripple v-slot:[`header.data-table-select`]="{}">
                    <v-simple-checkbox
                      :value="ownersItems.length == 0 ? false : ownersSelected.length == ownersItems.length"
                      :indeterminate="ownersSelected.length > 0 && ownersSelected.length != ownersItems.length"
                      @click="ownersSelected.length == ownersItems.length ? ownersSelected = [] : ownersSelected = [...ownersItems]">
                    </v-simple-checkbox>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>

            <!-- DEPLOYMENTS -->
            <v-card v-show="tabs==1" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text subtitle-1">DEPLOYMENTS</v-toolbar-title>
              </v-toolbar>
              <v-card-text>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.deployments_enabled" label="Access Deployments" color="info" style="margin-top:0px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enabled" v-model="group.deployments_basic" label="BASIC" color="#eb974e" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enabled" v-model="group.deployments_pro" label="PRO" color="rgb(235, 95, 93)" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">
                  LIMITS
                <v-tooltip right>
                  <template v-slot:activator="{ on }">
                    <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                  </template>
                  <span>
                    <b>Coins per Deployment</b>: How many coins will be consumed for every deployment.
                    <br>
                    <b>Concurrent Deployments</b>: Maximum concurrent deployments across all users in the group.
                    <br>
                    <b>Execution Threads</b>: This option is used to increase the parallelization factor and therefore reduce the execution time needed to finish a deployment.
                    <br>
                    <b>Execution Timeout</b>: Maximum execution time per query (in seconds). This field is optional and can be left blank.
                  </span>
                </v-tooltip>
                </div>
                <v-text-field v-model="group.deployments_coins" label="Coins per Deployment" :rules="[v => v == parseInt(v) && v >= 0 || '']" required style="margin-top:25px; padding-top:0px;"></v-text-field>
                <v-text-field v-model="group.deployments_execution_concurrent" label="Concurrent Deployments" :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-top:0px; padding-top:0px;"></v-text-field>
                <v-text-field v-model="group.deployments_execution_threads" label="Execution Threads" :rules="[v => v == parseInt(v) && v > 0 || '']" required style="margin-top:0px; padding-top:0px;"></v-text-field>
                <v-text-field v-model="group.deployments_execution_timeout" label="Execution Timeout" :rules="[v => v ? v == parseInt(v) && v > 0 : true || '']" style="margin-top:0px; padding-top:0px;"></v-text-field>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">
                  RETENTION
                <v-tooltip right>
                  <template v-slot:activator="{ on }">
                    <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                  </template>
                  <span>
                    <b>Expiration Time</b>: The amount of time that has to pass before deleting old deployments. This option does not apply when the Amazon S3 storage is enabled.
                  </span>
                </v-tooltip>
                </div>
                <v-select v-model="group.deployments_expiration_days" :items="[{id: 0, text: 'Never'}, {id: 1, text: '1 Day'}, {id: 7, text: '1 Week'}, {id: 30, text: '1 Month'}, {id: 90, text: '3 Months'}, {id: 180, text: '6 Months'}, {id: 365, text: '1 Year'}]" item-value="id" item-text="text" label="Expiration Time" style="margin-top:15px"></v-select>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">
                  SLACK
                  <v-tooltip right>
                    <template v-slot:activator="{ on }">
                      <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                    </template>
                    <span>
                      Send a <span class="font-weight-medium" style="color:rgb(250, 130, 49);">Slack</span> message everytime a deployment finishes.
                    </span>
                  </v-tooltip>
                </div>
                <v-switch v-model="group.deployments_slack_enabled" label="Enable Notifications" color="info" style="margin-top:0px" hide-details></v-switch>
                <div v-if="group.deployments_slack_enabled">
                  <v-text-field v-model="group.deployments_slack_name" label="Channel Name" :rules="[v => !!v || '']" style="margin-top:15px"></v-text-field>
                  <v-text-field v-model="group.deployments_slack_url" label="Webhook URL" :rules="[v => !!v && (v.startsWith('http://') || v.startsWith('https://')) || '']" style="padding-top:0px;"></v-text-field>
                  <v-btn :loading="loading" @click="testSlack('deployments')" color="info">Test Slack</v-btn>
                </div>
              </v-card-text>
            </v-card>

            <!-- MONITORING -->
            <v-card v-show="tabs==2" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text subtitle-1">MONITORING</v-toolbar-title>
              </v-toolbar>
              <v-card-text>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.monitoring_enabled" label="Access Monitoring" color="info" style="margin-top:0px; margin-bottom:15px" hide-details></v-switch>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">LIMITS</div>
                <v-text-field v-model="group.monitoring_interval" :rules="[v => v == parseInt(v) && v > 9 || '']" label="Data Collection Interval (seconds)" required hide-details></v-text-field>
              </v-card-text>
            </v-card>

            <!-- UTILS -->
            <v-card v-show="tabs==3" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text subtitle-1">UTILS</v-toolbar-title>
              </v-toolbar>
              <v-card-text>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.utils_enabled" label="Access Utils" color="info" style="margin-top:0px; margin-bottom:15px" hide-details></v-switch>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">
                  LIMITS
                  <v-tooltip right>
                    <template v-slot:activator="{ on }">
                      <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                    </template>
                    <span>
                      <b>Coins per Execution</b>: Required coins needed to perform Imports, Exports and Clones.
                      <br>
                      <b>Concurrent Executions</b>: Maximum concurrent executions (Imports, Exports, Clones) across all users in the group.
                      <br>
                      <b>Maximum Size</b>: The maximum allowed size to perform File Imports. This field is optional and can be left blank.
                    </span>
                  </v-tooltip>
                </div>
                <v-text-field v-model="group.utils_coins" label="Coins per Execution" :rules="[v => v == parseInt(v) && v >= 0 || '']" required style="margin-top:10px" hide-details></v-text-field>
                <v-text-field v-model="group.utils_concurrent" label="Concurrent Executions" :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-top:10px" hide-details></v-text-field>
                <v-text-field v-model="group.utils_limit" label="Maximum Size (MB)" :rules="[v => v ? v == parseInt(v) && v > 0 : true || '']" style="margin-top:10px" hide-details></v-text-field>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-top:20px; margin-bottom:10px">
                  SLACK
                  <v-tooltip right>
                    <template v-slot:activator="{ on }">
                      <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                    </template>
                    <span>
                      Send a <span class="font-weight-medium" style="color:rgb(250, 130, 49);">Slack</span> message everytime an import, export or clone finishes.
                    </span>
                  </v-tooltip>
                </div>
                <v-switch v-model="group.utils_slack_enabled" label="Enable Notifications" color="info" style="margin-top:0px;" hide-details></v-switch>
                <div v-if="group.utils_slack_enabled">
                  <v-text-field v-model="group.utils_slack_name" label="Channel Name" :rules="[v => !!v || '']" style="margin-top:15px" hide-details></v-text-field>
                  <v-text-field v-model="group.utils_slack_url" label="Webhook URL" :rules="[v => !!v && (v.startsWith('http://') || v.startsWith('https://')) || '']" style="margin-top:10px"></v-text-field>
                  <v-btn :loading="loading" @click="testSlack('utils')" color="info">Test Slack</v-btn>
                </div>
              </v-card-text>
            </v-card>

            <!-- CLIENT -->
            <v-card v-show="tabs==4" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text subtitle-1">CLIENT</v-toolbar-title>
              </v-toolbar>
              <v-card-text>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.client_enabled" label="Access Client" color="info" style="margin-top:0px; margin-bottom:15px" hide-details></v-switch>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px">
                  LIMITS
                  <v-tooltip right>
                  <template v-slot:activator="{ on }">
                    <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                  </template>
                  <span>
                    <b>Execution Timeout Mode</b>: The type of queries that will be affected by the execution timeout.
                    <br>
                    <b>Execution Timeout Value</b>: Maximum execution time per query (in seconds).
                    <br>
                    <b>Execution Rows</b>: Maximum number of rows returned by SELECTs.
                  </span>
                </v-tooltip>
                </div>
                <v-switch v-model="group.client_limits" label="Apply Limits" color="#fa8231" style="margin-top:0px" hide-details></v-switch>
                <v-select v-if="group.client_limits" v-model="group.client_limits_timeout_mode" :items="[{id: 1, name: 'All Queries'}, {id: 2, name: 'Only SELECTs'}]" item-value="id" item-text="name" label="Execution Timeout Mode" required :rules="[v => !!v || '']" style="margin-top:15px" hide-details></v-select>
                <v-text-field v-if="group.client_limits" v-model="group.client_limits_timeout_value" label="Execution Timeout Value" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-top:10px" hide-details></v-text-field>
                <v-text-field v-if="group.client_limits" v-model="group.client_limits_rows" label="Execution Rows" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-top:10px" hide-details></v-text-field>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-top:15px; margin-bottom:10px">TRACKING</div>
                <v-switch v-model="group.client_tracking" label="Track Queries" color="#fa8231" style="margin-top:0px" hide-details></v-switch>
                <v-select v-if="group.client_tracking" v-model="group.client_tracking_mode" :items="[{id: 1, name: 'All Queries'}, {id: 2, name: 'All Queries (exclude SELECT, SHOW and USE)'}]" item-value="id" item-text="name" label="Tracking Mode" required :rules="[v => !!v || '']" style="margin-top:15px" hide-details></v-select>
                <v-text-field v-if="group.client_tracking" v-model="group.client_tracking_retention" label="Tracking Retention Days" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-top:10px" hide-details></v-text-field>
              </v-card-text>
            </v-card>

            <div style="margin-top:20px;">
              <v-btn color="#00b16a" @click="submitGroup()">Confirm</v-btn>
              <router-link class="nav-link" to="/admin/groups">
                <v-btn color="#EF5354" @click="dialog=false" style="margin-left:5px">Cancel</v-btn>
              </router-link>
            </div>
          </v-form>
        </v-flex>      
      </v-card-text>
    </v-card>

    <!---------------------->
    <!-- Inventory Owners -->
    <!---------------------->
    <v-dialog v-model="ownersDialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ ownersDialogOptions.icon }}</v-icon>{{ ownersDialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="ownersDialog = false"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px">
                  <div v-if="ownersDialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important">{{ ownersDialogOptions.text }}</div>
                  <v-card v-if="ownersDialogOptions.mode == 'new'">
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text subtitle-1">USERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="ownersDialogSearch" @input="onOwnersSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <div v-if="ownersDialogItems.length == 0" class="body-2" style="margin-top:15px; text-align:center; color:rgb(211, 211, 211);">{{ ownersDialogSearch.length != 0 ? 'This search returned no results' : 'This group does not contain users or all users have already been added to owners' }}</div>
                    <v-list flat dense>
                      <v-list-item-group multiple>
                        <v-list-item v-for="item in ownersDialogItems" :key="item.username" dense @click="onOwnersClick(item)" @contextmenu="$event.preventDefault()">
                          <template>
                            <v-list-item-action>
                              <v-checkbox :input-value="ownersDialogSelected.includes(item.username)"></v-checkbox>
                            </v-list-item-action>
                            <v-list-item-content>
                              <v-list-item-title>{{ item.username }}</v-list-item-title>
                              <v-list-item-subtitle>{{ item.email }}</v-list-item-subtitle>
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
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn :disabled="ownersDialogOptions.mode == 'new' && this.ownersDialogSelected.length == 0" :loading="loading" @click="ownersDialogSubmit" color="#00b16a">{{ ownersDialogOptions.button1 }}</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="ownersDialog = false" color="#EF5354">{{ ownersDialogOptions.button2 }}</v-btn>
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
import axios from 'axios';

export default {
  data: () => ({
    mode: '',
    // +--------+
    // | GROUPS |
    // +--------+
    group: {
      inventory_enabled: false,
      deployments_enabled: false,
      deployments_basic: false,
      deployments_pro: false,
      deployments_coins: 10,
      deployments_execution_concurrent: 1,
      deployments_execution_threads: 10,
      deployments_execution_timeout: null,
      deployments_expiration_days: 0,
      deployments_slack_enabled: false,
      deployments_slack_name: '',
      deployments_slack_url: '',
      monitoring_enabled: false,
      monitoring_interval: 10,
      utils_enabled: false,
      utils_coins: 10,
      utils_concurrent: 1,
      utils_limit: null,
      utils_export_limit: null,
      utils_slack_enabled: false,
      utils_slack_name: '',
      utils_slack_url: '',
      client_enabled: false,
      client_tracking: false,
      client_tracking_retention: 1,
      client_tracking_mode: 1,
    },
    toolbar_title: '',
    form_valid: false,
    loading: false,

    // Inventory - Owners
    inventoryOwners: [],
    ownersItems: [],
    ownersSearch: '',
    ownersSelected: [],
    ownersHeaders: [
      { text: 'Username', align: 'left', value: 'username' },
      { text: 'Email', align: 'left', value: 'email' }
    ],

    // Inventory - Owners Dialog
    ownersDialog: false,
    ownersDialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
    ownersDialogRawItems: [],
    ownersDialogItems: [],
    ownersDialogSelected: [],
    ownersDialogSearch: '',

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
      this.mode = this.$route.params.mode
      this.group['id'] = this.$route.params.id
      this.toolbar_title = this.mode.toUpperCase() + ' GROUP'
      if (['edit','clone'].includes(this.mode)) this.getGroup()
    },
    // +--------+
    // | GROUPS |
    // +--------+
    getGroup() {
      this.loading = true
      axios.get('/admin/groups', { params: { groupID: this.group['id'] } })
        .then((response) => {
          if (response.data.group.length == 0) this.$router.push('/admin/groups')
          else {
            this.group = {...response.data.group[0]}
            this.inventoryOwners = response.data.owners
            if (this.mode == 'edit') this.ownersItems = response.data.owners.filter(x => x.owner)
          }
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    submitGroup() {
      this.loading = true
      if (['new','clone'].includes(this.mode)) this.newGroupSubmit()
      else this.editGroupSubmit()
    },
    newGroupSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      // Parse nullable values
      if (!this.group.deployments_execution_timeout) this.group.deployments_execution_timeout = null
      if (!this.group.utils_limit) this.group.utils_limit = null
      if (!this.group.utils_export_limit) this.group.utils_export_limit = null
      // Add group to the DB
      const payload = {
        mode: this.mode,
        group: JSON.stringify(this.group),
        owners: {
          add: this.ownersItems.map(x => x.username),
          del: [],
        },
      }
      axios.post('/admin/groups', payload)
        .then((response) => {
          this.$router.push({ name: 'admin.groups', params: { msg: response.data.message, color: '#00b16a' }})
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    editGroupSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      // Parse nullable values
      if (!this.group.deployments_execution_timeout) this.group.deployments_execution_timeout = null
      if (!this.group.utils_limit) this.group.utils_limit = null
      if (!this.group.utils_export_limit) this.group.utils_export_limit = null
      // Edit group to the DB
      const payload = {
        group: JSON.stringify(this.group),
        owners: {
          add: this.ownersItems.filter(x => this.inventoryOwners.some(y => y.username == x.username && !y.owner)).map(x => x.username),
          del: this.inventoryOwners.filter(x => x.owner && !this.ownersItems.some(y => y.username == x.username)).map(x => x.username)
        }
      }
      axios.put('/admin/groups', payload)
        .then((response) => {
          this.$router.push({ name: 'admin.groups', params: { msg: response.data.message, color: '#00b16a' }})
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    newOwners() {
      var ownersDialogOptions = {
      'mode': 'new',
        'title': 'NEW OWNERS',
        'icon': 'fas fa-plus',
        'text': '',
        'button1': 'Confirm',
        'button2': 'Cancel'
      }
      this.showDialog(ownersDialogOptions)
    },
    removeOwners() {
      var ownersDialogOptions = {
        'mode': 'delete',
        'title': 'REMOVE OWNERS',
        'icon': 'fas fa-minus',
        'text': 'Are you sure you want to remove the selected owners?',
        'button1': 'Confirm',
        'button2': 'Cancel'
      }
      this.showDialog(ownersDialogOptions)
    },
    showDialog(options) {
      this.ownersDialogOptions = options
      this.ownersDialogSearch = ''
      this.ownersDialogSelected = []
      this.ownersDialogRawItems = this.inventoryOwners.filter(x => !x.owner).filter(x => !this.ownersItems.some(y => y.username == x.username))
      this.ownersDialogItems = this.ownersDialogRawItems.slice(0)
      this.ownersDialog = true
    },
    onOwnersSearch(value) {
      if (value.length == 0) this.ownersDialogItems = this.ownersDialogRawItems.slice(0)
      else this.ownersDialogItems = this.ownersDialogRawItems.filter(x => x.username.includes(value) || x.email.includes(value))
    },
    onOwnersClick(item) {
      const index = this.ownersDialogSelected.findIndex(x => x == item.username)
      if (index > -1) this.ownersDialogSelected.splice(index, 1)
      else this.ownersDialogSelected.push(item.username)
    },
    ownersDialogSubmit() {
      if (this.ownersDialogOptions.mode == 'new') {
        for (let owner of this.ownersDialogSelected) {
          let obj = JSON.parse(JSON.stringify(this.ownersDialogRawItems.find(x => x.username == owner)))
          delete obj['owner']
          this.ownersItems.push(obj)
        }
      }
      else if (this.ownersDialogOptions.mode == 'delete') {
        this.ownersItems = this.ownersItems.filter(x => !this.ownersSelected.some(y => y.username == x.username))
        this.ownersSelected = []
      }
      this.ownersDialog = false
    },
    testSlack(section) {
      this.loading = true
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      // Test Slack Webhook URL
      const payload = {
        webhook_url: (section == 'deployments') ? this.group.deployments_slack_url : this.group.utils_slack_url
      }
      axios.get('/admin/groups/slack', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    goBack() {
      this.$router.push('/admin/groups')
    },
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
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
      })
    }
  }
}
</script>