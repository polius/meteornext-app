<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">{{ toolbar_title }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/admin/groups"><v-btn icon><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn></router-link>
      </v-toolbar>
      <v-card-text>
        <v-flex>
          <v-form ref="form" v-model="form_valid">
            <!-- INFO -->
            <div class="title font-weight-regular white--text" style="margin-bottom:5px;">INFO</div>
            <v-text-field ref="focus" v-model="group.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
            <v-text-field v-model="group.description" :rules="[v => !!v || '']" label="Description" required style="padding-top:0px; margin-top:0px;"></v-text-field>
          
            <!-- COINS -->
            <div class="title font-weight-regular white--text" style="margin-bottom:5px;">COINS</div>
            <v-text-field v-model="group.coins_day" label="Coins per day" :rules="[v => !!v || '', v => !isNaN(parseFloat(v)) && isFinite(v) && v >= 0 || '']" required></v-text-field>
            <v-text-field v-model="group.coins_max" label="Maximum coins" :rules="[v => !!v || '', v => !isNaN(parseFloat(v)) && isFinite(v) && v >= 0 || '']" required style="margin-top:0px; padding-top:0px;"></v-text-field>
            <v-text-field v-model="group.coins_execution" label="Coins per execution" :rules="[v => !!v || '', v => !isNaN(parseFloat(v)) && isFinite(v) && v >= 0 || '']" required style="margin-top:0px; padding-top:0px;"></v-text-field>

            <!-- DEPLOYMENTS -->
            <div>
              <v-tabs background-color="#263238" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
                <v-tabs-slider></v-tabs-slider>
                <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>DEPLOYMENTS</span></v-tab>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-tab><span class="pl-2 pr-2">Environments</span></v-tab>
                <v-tab><span class="pl-2 pr-2">Regions</span></v-tab>
                <v-tab><span class="pl-2 pr-2">Servers</span></v-tab>
                <v-tab><span class="pl-2 pr-2">Auxiliary Connections</span></v-tab>
                <v-tab><span class="pl-2 pr-2">Slack</span></v-tab>                
              </v-tabs>
            </div>

            <v-card v-if="tabs==0" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">DEPLOYMENTS</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.deployments_enable" label="Perform Deployments" style="margin-top:0px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enable" v-model="group.deployments_basic" label="BASIC" color="primary" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enable" v-model="group.deployments_pro" label="PRO" color="primary" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enable" v-model="group.deployments_inbenta" label="INBENTA" color="primary" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>

                <v-switch v-model="group.deployments_edit" label="Change Deployment Settings" style="margin-top:0px; margin-bottom:15px;" hide-details></v-switch>
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">
                  LIMITS
                <v-tooltip right>
                  <template v-slot:activator="{ on }">
                    <v-icon small style="margin-left:5px;" v-on="on">fas fa-question-circle</v-icon>
                  </template>
                  <span>Execution Plan Factor: Sets the maximum scanned rows allowed</span>
                </v-tooltip>
                </div>
                <v-switch v-model="group_epf_switch" label="Limit Queries Execution" style="margin-top:0px; margin-bottom:25px;" hide-details></v-switch>
                <v-text-field v-if="group_epf_switch" v-model="group.deployments_execution_plan_factor" label="Execution Plan Factor" :rules="[v => !!v || '', v => !isNaN(parseFloat(v)) && isFinite(v) && v > 0 || '']" required style="margin-top:0px; padding-top:0px;"></v-text-field>
                <v-text-field v-model="group.deployments_execution_threads" label="Execution Threads" :rules="[v => !!v || '', v => !isNaN(parseFloat(v)) && isFinite(v) && v > 0 && v < 100 || 'A number between: 1 - 99']" required style="margin-top:0px; padding-top:0px;"></v-text-field>
              </v-card-text>
            </v-card>

            <!-- environments -->
            <v-card v-if="tabs==1" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">Environments</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                <v-btn text @click='newEnvironment()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                <v-btn v-if="environment_selected.length == 1" text @click="editEnvironment()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                <v-btn v-if="environment_selected.length > 0" text @click='deleteEnvironment()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                </v-toolbar-items>
                <v-text-field v-model="environment_search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
              </v-toolbar>
              <v-divider></v-divider>
              <v-data-table v-model="environment_selected" :headers="environment_headers" :items="environment_items" :search="environment_search" :loading="loading" loading-text="Loading... Please wait" item-key="name" hide-default-footer show-select class="elevation-1">
              </v-data-table>
            </v-card>

            <!-- regions -->
            <v-card v-if="tabs==2" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">Regions</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                <v-btn text @click='newRegion()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                <v-btn v-if="region_selected.length == 1" text @click="editRegion()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                <v-btn v-if="region_selected.length > 0" text @click='deleteRegion()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                </v-toolbar-items>
                <v-text-field v-model="region_search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
              </v-toolbar>
              <v-divider></v-divider>
              <v-data-table v-model="region_selected" :headers="region_headers" :items="region_items" :search="region_search" :loading="loading" loading-text="Loading... Please wait" item-key="name" :hide-default-header="region_items.length == 0" hide-default-footer show-select class="elevation-1">
                <template v-slot:item.cross_region="props">
                  <v-icon v-if="props.item.cross_region" small color="success" style="margin-left:28px">fas fa-check</v-icon>
                  <v-icon v-else small color="error" style="margin-left:28px">fas fa-times</v-icon>
                </template>
                <template v-slot:item.password="props">
                  <v-icon v-if="props.item.cross_region && (props.item.password || '').length != 0" small color="success" style="margin-left:20px">fas fa-check</v-icon>
                  <v-icon v-else-if="props.item.cross_region" small color="error" style="margin-left:20px">fas fa-times</v-icon>
                </template>
                <template v-slot:item.key="props">
                  <v-icon v-if="props.item.cross_region && (props.item.key || '').length != 0" small color="success" style="margin-left:20px">fas fa-check</v-icon>
                  <v-icon v-else-if="props.item.cross_region" small color="error" style="margin-left:20px">fas fa-times</v-icon>
                </template>
                <template v-slot:no-results>
                  <v-alert :value="true" color="error" icon="warning" style="margin-top:15px;">
                    Your search for "{{ search }}" found no results.
                  </v-alert>
                </template>
              </v-data-table>
            </v-card>

            <!-- servers -->
            <v-card v-if="tabs==3" style="margin-bottom:10px;">
            <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
              <v-toolbar-title class="white--text">Servers</v-toolbar-title>
              <v-divider class="mx-3" inset vertical></v-divider>
              <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                <v-btn text @click='newServer()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                <v-btn v-if="server_selected.length == 1" text @click="editServer()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                <v-btn v-if="server_selected.length > 0" text @click='deleteServer()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
              </v-toolbar-items>
              <v-text-field v-model="server_search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
            </v-toolbar>
            <v-divider></v-divider>
            <v-data-table v-model="server_selected" :headers="server_headers" :items="server_items" :search="server_search" :loading="loading" loading-text="Loading... Please wait" item-key="name" :hide-default-header="server_items.length == 0" hide-default-footer show-select class="elevation-1">
            </v-data-table>
            </v-card>

            <!-- auxiliary connections -->
            <v-card v-if="tabs==4" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">Auxiliary Connections</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
                  <v-btn text @click='newAuxiliary()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                  <v-btn v-if="auxiliary_selected.length == 1" text @click="editAuxiliary()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                  <v-btn v-if="auxiliary_selected.length > 0" text @click='deleteAuxiliary()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                </v-toolbar-items>
                <v-text-field v-model="auxiliary_search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
              </v-toolbar>
              <v-divider></v-divider>
              <v-data-table v-model="auxiliary_selected" :headers="auxiliary_headers" :items="auxiliary_items" :search="auxiliary_search" :loading="loading" loading-text="Loading... Please wait" item-key="name" :hide-default-header="auxiliary_items.length == 0" hide-default-footer show-select class="elevation-1">
              </v-data-table>
            </v-card>

            <!-- slack -->
            <v-card v-if="tabs==5">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">Slack</v-toolbar-title>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text style="padding-bottom:0px;">
                <v-text-field :loading="loading" :disabled="loading" v-model="slack.channel_name" label="Channel Name"></v-text-field>
                <v-text-field :loading="loading" :disabled="loading" v-model="slack.webhook_url" label="Webhook URL" style="padding-top:0px;"></v-text-field>
                <v-switch :disabled="loading" v-model="slack.enabled" label="Enable Notifications" style="margin-top:0px;"></v-switch>
              </v-card-text>
            </v-card>

            <div style="margin-top:20px;">
              <v-btn color="success" @click="submitGroup()">Confirm</v-btn>
              <router-link class="nav-link" to="/admin/groups">
                <v-btn color="error" @click="dialog=false" style="margin-left:10px">Cancel</v-btn>
              </router-link>
            </div>
          </v-form>
        </v-flex>      
      </v-card-text>
    </v-card>
    <!--
    +--------------+
    | ENVIRONMENTS |
    +--------------+
    -->
    <v-dialog v-model="environment_dialog" persistent max-width="768px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ environment_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="environment_form" style="margin-top:15px; margin-bottom:20px;" v-model="environment_dialog_valid">
                  <v-text-field ref="environment_focus" v-if="environment_mode!='delete'" v-on:keydown.enter.prevent="submitEnvironment()" v-model="environment_item.name" :rules="[v => !!v || '']" label="Environment Name" required></v-text-field>
                  <div style="padding-bottom:10px" v-if="environment_mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected environments?</div>
                  <v-divider></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn :loading="loading" color="success" @click="submitEnvironment()">Confirm</v-btn>
                    <v-btn :disabled="loading" color="error" @click="environment_dialog=false" style="margin-left:10px">Cancel</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--
    +---------+
    | REGIONS |
    +---------+
    -->
    <v-dialog v-model="region_dialog" persistent max-width="768px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ region_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="region_form" v-if="region_mode!='delete'" v-model="region_dialog_valid" style="margin-top:15px; margin-bottom:20px;">
                  <!-- METADATA -->
                  <div class="title font-weight-regular">Metadata</div>
                  <v-text-field ref="region_focus" v-model="region_item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-select v-model="region_item.environment" :items="environments" :rules="[v => !!v || '']" label="Environment" required style="margin-top:0px; padding-top:0px;"></v-select>
                  <!-- SSH -->
                  <v-switch v-model="region_item.cross_region" label="Cross Region" style="margin-top:0px;" hide-details></v-switch>
                  <div v-if="region_item.cross_region">
                    <div class="title font-weight-regular">SSH</div>
                    <v-text-field v-model="region_item.hostname" :rules="[v => !!v || '']" label="Hostname"></v-text-field>
                    <v-text-field v-model="region_item.username" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="region_item.password" label="Password" style="padding-top:0px;"></v-text-field>
                    <v-textarea v-model="region_item.key" label="Private Key" style="padding-top:0px;"></v-textarea>
                  </div>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="region_mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected regions?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="success" @click="submitRegion()">Confirm</v-btn>
                  <v-btn :disabled="loading" color="error" @click="region_dialog=false" style="margin-left:10px">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--
    +---------+
    | SERVERS |
    +---------+
    -->
    <v-dialog v-model="server_dialog" persistent max-width="768px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ server_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="server_form" v-if="server_mode!='delete'" v-model="server_dialog_valid" style="margin-top:15px; margin-bottom:20px;">
                  <!-- METADATA -->
                  <div class="title font-weight-regular">Metadata</div>
                  <v-text-field ref="server_focus" v-model="server_item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-select v-model="server_item.environment" :items="environments" :rules="[v => !!v || '']" label="Environment" v-on:change="refreshRegions()" required style="margin-top:0px; padding-top:0px;"></v-select>
                  <v-select v-model="server_item.region" :items="regions" :rules="[v => !!v || '']" label="Region" required style="margin-top:0px; padding-top:0px;"></v-select>
                  <!-- SQL -->
                  <div class="title font-weight-regular" style="padding-top:10px;">SQL</div>
                  <v-text-field v-model="server_item.hostname" :rules="[v => !!v || '']" label="Hostname" required></v-text-field>
                  <v-text-field v-model="server_item.username" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;" required></v-text-field>
                  <v-text-field v-model="server_item.password" :rules="[v => !!v || '']" label="Password" style="padding-top:0px;" required hide-details></v-text-field>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="server_mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected servers?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="success" @click="submitServer()">Confirm</v-btn>
                  <v-btn :disabled="loading" color="error" @click="server_dialog=false" style="margin-left:10px">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--
    +-----------------------+
    | AUXILIARY CONNECTIONS |
    +-----------------------+
    -->
    <v-dialog v-model="auxiliary_dialog" persistent max-width="768px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ auxiliary_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="auxiliary_form" v-if="auxiliary_mode!='delete'" v-model="auxiliary_dialog_valid" style="margin-top:15px; margin-bottom:20px;">
                  <!-- METADATA -->
                  <div class="title font-weight-regular">Metadata</div>
                  <v-text-field ref="auxiliary_focus" v-model="auxiliary_item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <!-- SQL -->
                  <div class="title font-weight-regular" style="padding-top:10px;">SQL</div>
                  <v-text-field v-model="auxiliary_item.hostname" :rules="[v => !!v || '']" label="Hostname"></v-text-field>
                  <v-text-field v-model="auxiliary_item.username" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="auxiliary_item.password" :rules="[v => !!v || '']" label="Password" style="padding-top:0px;" hide-details></v-text-field>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="auxiliary_mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected auxiliary connections?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="success" @click="submitAuxiliary()">Confirm</v-btn>
                  <v-btn :disabled="loading" color="error" @click="auxiliary_dialog=false" style="margin-left:10px">Cancel</v-btn>
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
/* eslint-disable */
import axios from 'axios';

export default {
  data: () => ({
    // +--------+
    // | GROUPS |
    // +--------+
    group: { 
      'deployments_enable': false,
      'deployments_basic': false,
      'deployments_pro': false,
      'deployments_inbenta': false,
      'deployments_edit': false,
      'deployments_execution_plan_factor': 0,
      'deployments_execution_threads': 10 
    },
    group_epf_switch: false,
    toolbar_title: '',
    form_valid: false,
    loading: false,

    // +------+
    // | TABS |
    // +------+
    tabs: null,

    // +--------------+
    // | ENVIRONMENTS |
    // +--------------+
    environment_headers: [{ text: 'Name', value: 'name', align: 'left', sortable: 'false' }],
    environment_items: [],
    environment_selected: [],
    environment_search: '',
    environment_item: { name: '' },
    environment_mode: '',
    environment_dialog: false,
    environment_dialog_title: '',
    environment_dialog_valid: false,
    environments: [],

    // +---------+
    // | REGIONS |
    // +---------+
    region_headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', align: 'left', value: 'environment' },
      { text: 'Cross Region', align: 'left', value: 'cross_region'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'},
      { text: 'Private Key', align: 'left', value: 'key'}
    ],
    region_items: [],
    region_selected: [],
    region_search: '',
    region_item: { name: '', environment: '', cross_region: false, hostname: '', username: '', password: '', key: '' },
    region_mode: '',
    region_dialog: false,
    region_dialog_title: '',
    region_dialog_valid: false,
    regions: [],

    // +---------+
    // | SERVERS |
    // +---------+
    server_headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', align: 'left', value: 'environment'},
      { text: 'Region', align: 'left', value: 'region'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    server_items: [],
    server_selected: [],
    server_search: '',
    server_item: { name: '', environment: '', region: '', hostname: '', username: '', password: '' },
    server_mode: '',
    server_dialog: false,
    server_dialog_title: '',
    server_dialog_valid: false,

    // +-----------------------+
    // | AUXILIARY CONNECTIONS |
    // +-----------------------+
    auxiliary_headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    auxiliary_items: [],
    auxiliary_selected: [],
    auxiliary_search: '',
    auxiliary_item: { name: '', hostname: '', username: '', password: '' },
    auxiliary_mode: '',
    auxiliary_dialog: false,
    auxiliary_dialog_title: '',
    auxiliary_dialog_valid: false,

    // +-------+
    // | SLACK |
    // +-------+
    slack: {
      channel_name: '',
      webhook_url: '',
      enabled: false
    },

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  props: ['groupID'],
  created() {
    if (typeof this.groupID === "undefined") this.$router.push({ name: 'admin.groups' })
    else if (this.groupID.length == 0) this.toolbar_title = 'NEW GROUP'
    else {
      this.toolbar_title = 'EDIT GROUP'
      this.getGroup()
    }
  },
  methods: {
    // +--------+
    // | GROUPS |
    // +--------+
    getGroup() {
      axios.get('/admin/groups', { params: { groupID: this.groupID } })
        .then((response) => {
          this.group = response.data.group[0]
          this.group_epf_switch = this.group['deployments_epf'] > 0
          if (this.group.deployments_epf == 0) this.group.deployments_epf = 1000
          this.environment_items = response.data.environments.data
          this.region_items = response.data.regions.data.regions
          this.server_items = response.data.servers.data.servers
          this.auxiliary_items = response.data.auxiliary.data
          if (response.data.slack.data.length > 0) this.slack = response.data.slack.data[0]
          this.refreshEnvironments()
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    submitGroup() {
      this.loading = true
      if (this.groupID.length == 0) this.newGroupSubmit()
      else this.editGroupSubmit()
    },
    newGroupSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
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
          this.notification(response.data.message, 'success')
          // Add item in the data table
          this.$router.push({ name: 'admin.groups' })
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
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

      // Get the Execution Plan Factor
      this.group['deployments_epf'] = (this.group_epf_switch) ? this.group['deployments_epf'] : 0

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
          this.notification(response.data.message, 'success')
          // Add item in the data table
          this.$router.push({ name: 'admin.groups' })
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    // +--------------+
    // | ENVIRONMENTS |
    // +--------------+
    newEnvironment() {
      this.environment_mode = 'new'
      this.environment_item = { name: '' }
      this.environment_dialog_title = 'New Environment'
      this.environment_dialog = true
    },
    editEnvironment() {
      this.environment_mode = 'edit'
      this.environment_item = JSON.parse(JSON.stringify(this.environment_selected[0]))
      this.environment_dialog_title = 'Edit Environment'
      this.environment_dialog = true
    },
    deleteEnvironment() {
      this.environment_mode = 'delete'
      this.environment_dialog_title = 'Delete Environment'
      this.environment_dialog = true
    },
    submitEnvironment() {
      if (this.environment_mode == 'new') this.newEnvironmentSubmit()
      else if (this.environment_mode == 'edit') this.editEnvironmentSubmit()
      else if (this.environment_mode == 'delete') this.deleteEnvironmentSubmit()
      // Refresh environments list
      this.refreshEnvironments()
    },
    newEnvironmentSubmit() {
      // Check if all fields are filled
      if (!this.$refs.environment_form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.environment_items.length; ++i) {
        if (this.environment_items[i]['name'] == this.environment_item.name) {
          this.notification('This environment currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.environment_items.push(this.environment_item)
      this.environment_dialog = false
    },
    editEnvironmentSubmit() {
      // Check if all fields are filled
      if (!this.$refs.environment_form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Get Item Position
      for (var i = 0; i < this.environment_items.length; ++i) {
        if (this.environment_items[i]['name'] == this.environment_selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.environment_items.length; ++j) {
        if (this.environment_items[j]['name'] == this.environment_item.name && this.environment_item.name != this.environment_selected[0]['name']) {
          this.notification('This environment currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.environment_items.splice(i, 1, this.environment_item)
      this.environment_selected = []
      this.environment_dialog = false
    },
    deleteEnvironmentSubmit() {
      // Check inconsistencies
      for (var i = 0; i < this.environment_selected.length; ++i) {
        for (var j = 0; j < this.region_items.length; ++j) {
          if (this.environment_selected[i]['name'] == this.region_items[j]['environment']) {
            this.notification("The environment '" + this.environment_selected[i]['name'] + "' has attached regions", 'error')
            this.environment_dialog = false
            return
          }
        }
      }
      // Remove environment in the data table
      while(this.environment_selected.length > 0) {
        var e = this.environment_selected.pop()
        for (var i = 0; i < this.environment_items.length; ++i) {
          if (this.environment_items[i]['name'] == e['name']) {
            // Delete Item
            this.environment_items.splice(i, 1)
            break
          }
        }
      }
      this.environment_dialog = false
    },
    refreshEnvironments() {
      this.environments = []
      for (var i in this.environment_items) this.environments.push(this.environment_items[i]['name'])
    },
    // +---------+
    // | REGIONS |
    // +---------+
    newRegion() {
      this.region_mode = 'new'
      this.region_item = { name: '', environment: '', cross_region: false, hostname: '', username: '', password: '', key: '' }
      this.region_dialog_title = 'New Region'
      this.region_dialog = true
    },
    editRegion() {
      this.region_mode = 'edit'
      this.region_item = JSON.parse(JSON.stringify(this.region_selected[0]))
      this.region_dialog_title = 'Edit Region'
      this.region_dialog = true
    },
    deleteRegion() {
      this.region_mode = 'delete'
      this.region_dialog_title = 'Delete Region'
      this.region_dialog = true
    },
    submitRegion() {
      if (this.region_mode == 'new') this.newRegionSubmit()
      else if (this.region_mode == 'edit') this.editRegionSubmit()
      else if (this.region_mode == 'delete') this.deleteRegionSubmit()
    },
    newRegionSubmit() {
      // Check if all fields are filled
      if (!this.$refs.region_form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.region_items.length; ++i) {
        if (this.region_items[i]['name'] == this.region_item.name) {
          this.notification('This region currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.region_items.push(this.region_item)
      this.region_dialog = false
    },
    editRegionSubmit() {
      // Check if all fields are filled
      if (!this.$refs.region_form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Get Item Position
        for (var i = 0; i < this.region_items.length; ++i) {
        if (this.region_items[i]['name'] == this.region_selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.region_items.length; ++j) {
        if (this.region_items[j]['name'] == this.region_item.name && this.region_item.name != this.region_selected[0]['name']) {
          this.notification('This region currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.region_items.splice(i, 1, this.region_item)
      this.region_selected = []
      this.region_dialog = false
    },
    deleteRegionSubmit() {
      // Check inconsistencies
      for (var i = 0; i < this.region_selected.length; ++i) {
        for (var j = 0; j < this.server_items.length; ++j) {
          if (this.region_selected[i]['name'] == this.server_items[j]['region']) {
            this.notification("The region '" + this.region_selected[i]['name'] + "' has attached servers", 'error')
            this.region_dialog = false
            return
          }
        }
      }
      // Remove region in the data table
      while(this.region_selected.length > 0) {
        var s = this.region_selected.pop()
        for (var i = 0; i < this.region_items.length; ++i) {
          if (this.region_items[i]['name'] == s['name']) {
            // Delete Item
            this.region_items.splice(i, 1)
            break
          }
        }
      }
      this.region_dialog = false
    },
    refreshRegions() {
      this.regions = []
      for (var i in this.region_items) {
        if (this.region_items[i]['environment'] == this.server_item.environment) {
          this.regions.push(this.region_items[i]['name'])
        }
      }
    },
    // +---------+
    // | SERVERS |
    // +---------+
    newServer() {
      this.server_mode = 'new'
      this.server_item = { name: '', environment: '', region: '', hostname: '', username: '', password: '' }
      this.server_dialog_title = 'New Server'
      this.server_dialog = true
    },
    editServer() {
      this.server_mode = 'edit'
      this.server_item = JSON.parse(JSON.stringify(this.server_selected[0]))
      this.server_dialog_title = 'Edit Server'
      this.server_dialog = true
    },
    deleteServer() {
      this.server_mode = 'delete'
      this.server_dialog_title = 'Delete Server'
      this.server_dialog = true
    },
    submitServer() {
      if (this.server_mode == 'new') this.newServerSubmit()
      else if (this.server_mode == 'edit') this.editServerSubmit()
      else if (this.server_mode == 'delete') this.deleteServerSubmit()
    },
    newServerSubmit() {
      // Check if all fields are filled
      if (!this.$refs.server_form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.server_items.length; ++i) {
        if (this.server_items[i]['name'] == this.server_item.name) {
          this.notification('This server currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.server_items.push(this.server_item)
      this.server_dialog = false
    },
    editServerSubmit() {
      // Check if all fields are filled
      if (!this.$refs.server_form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Get Item Position
        for (var i = 0; i < this.server_items.length; ++i) {
        if (this.server_items[i]['name'] == this.server_selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.server_items.length; ++j) {
        if (this.server_items[j]['name'] == this.server_item.name && this.server_item.name != this.server_selected[0]['name']) {
          this.notification('This server currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.server_items.splice(i, 1, this.server_item)
      this.server_selected = []
      this.server_dialog = false
    },
    deleteServerSubmit() {
      while(this.server_selected.length > 0) {
        var s = this.server_selected.pop()
        for (var i = 0; i < this.server_items.length; ++i) {
          if (this.server_items[i]['name'] == s['name']) {
            // Delete Item
            this.server_items.splice(i, 1)
            break
          }
        }
      }
      this.server_dialog = false
    },
    // +-----------------------+
    // | AUXILIARY CONNECTIONS |
    // +-----------------------+
    newAuxiliary() {
      this.auxiliary_mode = 'new'
      this.auxiliary_item = { name: '', hostname: '', username: '', password: '' }
      this.auxiliary_dialog_title = 'New Auxiliary Connection'
      this.auxiliary_dialog = true
    },
    editAuxiliary() {
      this.auxiliary_mode = 'edit'
      this.auxiliary_item = JSON.parse(JSON.stringify(this.auxiliary_selected[0]))
      this.auxiliary_dialog_title = 'Edit Auxiliary Connection'
      this.auxiliary_dialog = true
    },
    deleteAuxiliary() {
      this.auxiliary_mode = 'delete'
      this.auxiliary_dialog_title = 'Delete Auxiliary Connection'
      this.auxiliary_dialog = true
    },
    submitAuxiliary() {
      if (this.auxiliary_mode == 'new') this.newAuxiliarySubmit()
      else if (this.auxiliary_mode == 'edit') this.editAuxiliarySubmit()
      else if (this.auxiliary_mode == 'delete') this.deleteAuxiliarySubmit()
    },
    newAuxiliarySubmit() {
      // Check if all fields are filled
      if (!this.$refs.auxiliary_form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.auxiliary_items.length; ++i) {
        if (this.auxiliary_items[i]['name'] == this.auxiliary_item.name) {
          this.notification('This auxiliary Connection currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.auxiliary_items.push(this.auxiliary_item)
      this.auxiliary_dialog = false
    },
    editAuxiliarySubmit() {
      // Check if all fields are filled
      if (!this.$refs.auxiliary_form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Get Item Position
        for (var i = 0; i < this.auxiliary_items.length; ++i) {
        if (this.auxiliary_items[i]['name'] == this.auxiliary_selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.auxiliary_items.length; ++j) {
        if (this.auxiliary_items[j]['name'] == this.auxiliary_item.name && this.auxiliary_item.name != this.auxiliary_selected[0]['name']) {
          this.notification('This auxiliary Connection currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.auxiliary_items.splice(i, 1, this.auxiliary_item)
      this.auxiliary_selected = []
      this.auxiliary_dialog = false
    },
    deleteAuxiliarySubmit() {
      while(this.auxiliary_selected.length > 0) {
        var s = this.auxiliary_selected.pop()
        for (var i = 0; i < this.auxiliary_items.length; ++i) {
          if (this.auxiliary_items[i]['name'] == s['name']) {
            // Delete Item
            this.auxiliary_items.splice(i, 1)
            break
          }
        }
      }
      this.auxiliary_selected = []
      this.auxiliary_dialog = false
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
    },
    environment_dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.environment_form !== 'undefined') this.$refs.environment_form.resetValidation()
        if (typeof this.$refs.environment_focus !== 'undefined') this.$refs.environment_focus.focus()
      })
    },
    region_dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.region_form !== 'undefined') this.$refs.region_form.resetValidation()
        if (typeof this.$refs.region_focus !== 'undefined') this.$refs.region_focus.focus()
      })
    },
    server_dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.server_form !== 'undefined') this.$refs.server_form.resetValidation()
        if (typeof this.$refs.server_focus !== 'undefined') this.$refs.server_focus.focus()
      })
    },
    auxiliary_dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.auxiliary_form !== 'undefined') this.$refs.auxiliary_form.resetValidation()
        if (typeof this.$refs.auxiliary_focus !== 'undefined') this.$refs.auxiliary_focus.focus()
      })
    }
  }
}
</script>