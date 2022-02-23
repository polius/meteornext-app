<template>
  <div>
    <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="filter.search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
      <template v-ripple v-slot:[`header.data-table-select`]="{}">
        <v-simple-checkbox
          :value="items.length == 0 ? false : selected.length == items.length"
          :indeterminate="selected.length > 0 && selected.length != items.length"
          @click="selected.length == items.length ? selected = [] : selected = [...items]">
        </v-simple-checkbox>
      </template>
      <template v-slot:[`item.name`]="{ item }">
        <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
        <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
        <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
        {{ item.name }}
      </template>
      <template v-slot:[`item.region`]="{ item }">
        <v-icon v-if="item.region == null" small color="warning" title="This server does not have a region. Please edit it and add a region to this server.">fas fa-exclamation-triangle</v-icon>
        <v-btn v-else @click="openRegion(item.region_id)" text class="text-body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
          <v-icon small :title="item.region_shared ? item.region_secured ? 'Shared (Secured)' : 'Shared' : item.region_secured ? 'Personal (Secured)' : 'Personal'" :color="item.region_shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.region_secured ? 'padding-right:8px' : ''}`">{{ item.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
          <v-icon v-if="item.region_secured" :title="item.region_shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.region_shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
          {{ item.region }}
        </v-btn>
      </template>
      <template v-slot:[`item.usage`]="{ item }">
        <v-icon v-if="item.usage.includes('D')" title="Deployments" small color="#EF5354" style="margin-right:5px">fas fa-circle</v-icon>
        <v-icon v-if="item.usage.includes('M')" title="Monitoring" small color="#fa8231" style="margin-right:5px">fas fa-circle</v-icon>
        <v-icon v-if="item.usage.includes('U')" title="Utils" small color="#00b16a" style="margin-right:5px">fas fa-circle</v-icon>
        <v-icon v-if="item.usage.includes('C')" title="Client" small color="#8e44ad">fas fa-circle</v-icon>
      </template>
      <template v-slot:[`item.ssl`]="{ item }">
        <v-icon small :title="item.ssl ? 'SSL Enabled' : 'SSL Disabled'" :color="item.ssl ? '#00b16a' : '#EF5354'" style="margin-left:2px">fas fa-circle</v-icon>
      </template>
      <template v-slot:[`footer.prepend`]>
        <div v-if="disabledResources" class="text-body-2 font-weight-regular" style="margin:10px"><v-icon small color="warning" style="margin-right:10px; margin-bottom:2px">fas fa-exclamation-triangle</v-icon>Some servers are disabled. Consider the possibility of upgrading your license.</div>
      </template>
    </v-data-table>
    <!------------------->
    <!-- SERVER DIALOG -->
    <!------------------->
    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" title="Create the server only for a user" :color="!item.shared ? 'primary' : '#779ecb'" @click="personalClick" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" title="Create the server for all users in a group" :color="item.shared ? 'primary' : '#779ecb'" @click="sharedClick"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-checkbox v-if="mode != 'delete'" title="Prevent this resource from being edited and hide sensible data" v-model="item.secured" flat color="white" hide-details>
            <template v-slot:label>
              <div style="color:white">Secured</div>
            </template>
          </v-checkbox>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form v-if="mode != 'delete'" ref="form" style="margin-top:15px">
                  <v-row no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-autocomplete ref="group_id" @change="groupChanged" v-model="item.group_id" :items="groups" item-value="id" item-text="name" label="Group" :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-top:0px"></v-autocomplete>
                    </v-col>
                    <v-col v-if="!item.shared" style="margin-left:20px">
                      <v-autocomplete ref="owner_id" v-model="item.owner_id" @change="ownerChanged" :items="users" item-value="id" item-text="username" label="Owner" :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-top:0px"></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="6" style="padding-right:10px">
                      <v-text-field ref="name" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:10px">
                      <v-autocomplete :disabled="item.group_id == null" v-model="item.region_id" item-value="id" item-text="name" :rules="[v => !!v || '']" :items="regions" label="Region" required>
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-select v-model="item.engine" :items="Object.keys(engines)" label="Engine" :rules="[v => !!v || '']" required style="padding-top:0px;" v-on:change="selectEngine"></v-select>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-select v-model="item.version" :items="versions" label="Version" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                    </v-col>
                  </v-row>
                  <div style="margin-bottom:15px">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field v-model="item.hostname" :rules="[v => !!v || '']" label="Hostname" required style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field v-model="item.port" :rules="[v => v == parseInt(v) || '']" label="Port" required style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :rules="[v => !!v || '']" label="Username" required autocomplete="username" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" label="Password" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" style="padding-top:0px;" hide-details>
                      <template v-slot:[`append`]>
                        <v-btn title="Generate password" @click="generatePassword" icon><v-icon>mdi-key</v-icon></v-btn>
                        <v-btn :title="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword" icon><v-icon>{{ showPassword ? 'mdi-eye' : 'mdi-eye-off' }}</v-icon></v-btn>
                      </template>
                    </v-text-field>
                    <div v-if="(item.ssl_client_key == null || typeof item.ssl_client_key === 'object') && (item.ssl_client_certificate == null || typeof item.ssl_client_certificate === 'object') && (item.ssl_ca_certificate == null || typeof item.ssl_ca_certificate === 'object')">
                      <v-switch v-model="item.ssl" flat label="SSL Connection" hide-details style="margin-top:20px"></v-switch>
                      <v-row no-gutters v-if="item.ssl" style="margin-top:20px; margin-bottom:20px;">
                        <v-col style="padding-right:10px;">
                          <v-file-input v-model="item.ssl_client_key" filled dense label="Client Key" prepend-icon="" hide-details></v-file-input>
                        </v-col>
                        <v-col style="padding-right:5px; padding-left:5px;">
                          <v-file-input v-model="item.ssl_client_certificate" filled dense label="Client Certificate" prepend-icon="" hide-details></v-file-input>
                        </v-col>
                        <v-col style="padding-left:10px;">
                          <v-file-input v-model="item.ssl_ca_certificate" filled dense label="CA Certificate" prepend-icon="" hide-details></v-file-input>
                        </v-col>
                      </v-row>
                    </div>
                    <v-card v-else style="height:52px; margin-top:20px">
                      <v-row no-gutters>
                        <v-col cols="auto" style="display:flex; margin:15px">
                          <v-icon color="#00b16a" style="font-size:17px; margin-top:2px">fas fa-key</v-icon>
                        </v-col>
                        <v-col>
                          <div class="text-body-1" style="color:#00b16a; margin-top:15px">{{ 'Using a SSL connection (' + ssl_active + ')' }}</div>
                        </v-col>
                        <v-col cols="auto" class="text-right">
                          <v-btn @click="removeSSL" icon title="Remove SSL connection" style="margin:8px"><v-icon style="font-size:18px">fas fa-times</v-icon></v-btn>
                        </v-col>
                      </v-row>
                    </v-card>
                    <v-checkbox v-if="item.ssl" v-model="item.ssl_verify_ca" label="Verify server certificate against CA" hide-details></v-checkbox>
                    <v-select :disabled="item.group_id == null" outlined v-model="item.usage" :items="usage" :menu-props="{ top: true, offsetY: true }" label="Usage" multiple hide-details style="margin-top:20px"></v-select>
                  </div>
                </v-form>
                <div v-else class="subtitle-1" style="margin-bottom:12px">Are you sure you want to delete the selected servers?</div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:15px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :loading="loading" color="#00b16a" @click="submitServer()">CONFIRM</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="testConnection()">Test Connection</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!------------------->
    <!-- REGION DIALOG -->
    <!------------------->
    <v-dialog v-model="regionDialog" max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">REGION</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn readonly title="Create the region only for you" :color="!regionDialogItem.shared ? 'primary' : '#779ecb'" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn readonly title="Create the region for all users in your group" :color="regionDialogItem.shared ? 'primary' : '#779ecb'"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="regionDialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px">
                  <v-text-field ref="field" v-model="regionDialogItem.name" :rules="[v => !!v || '']" readonly label="Name" required hide-details style="margin-top:0px; padding-top:0px"></v-text-field>
                  <v-switch v-model="regionDialogItem.ssh_tunnel" readonly label="SSH Tunnel" color="info" hide-details style="margin-top:15px"></v-switch>
                  <div v-if="regionDialogItem.ssh_tunnel" style="margin-top:25px">
                    <v-row no-gutters>
                      <v-col cols="9" style="padding-right:10px">
                        <v-text-field ref="hostname" v-model="regionDialogItem.hostname" readonly :rules="[v => !!v || '']" label="Hostname" style="padding-top:0px; margin-top:0px"></v-text-field>
                      </v-col>
                      <v-col cols="3" style="padding-left:10px">
                        <v-text-field v-model="regionDialogItem.port" readonly :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px; margin-top:0px"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="regionDialogItem.username" readonly :rules="[v => !!v || '']" label="Username" autocomplete="username"  style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="regionDialogItem.password" readonly label="Password" :type="showRegionPassword ? 'text' : 'password'" autocomplete="new-password" style="padding-top:0px" hide-details>
                      <template v-slot:[`append`]>
                        <v-btn :title="showRegionPassword ? 'Hide password' : 'Show password'" @click="showRegionPassword = !showRegionPassword" icon><v-icon>{{ showRegionPassword ? 'mdi-eye' : 'mdi-eye-off' }}</v-icon></v-btn>
                      </template>
                    </v-text-field>
                  </div>
                  <!-- PKEY -->
                  <v-card v-if="regionDialogItem.key" style="height:52px; margin-top:15px">
                    <v-row no-gutters>
                      <v-col cols="auto" style="display:flex; margin:15px">
                        <v-icon color="#00b16a" style="font-size:17px; margin-top:2px">fas fa-key</v-icon>
                      </v-col>
                      <v-col>
                        <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a Private Key</div>
                      </v-col>
                    </v-row>
                  </v-card>
                  <!-- SECURED -->
                  <v-card v-if="regionDialogItem.secured" style="height:52px; margin-top:15px">
                    <v-row no-gutters>
                      <v-col cols="auto" style="display:flex; margin:15px">
                        <v-icon color="#EF5354" style="font-size:16px; margin-top:4px">fas fa-lock</v-icon>
                      </v-col>
                      <v-col>
                        <div class="text-body-1" style="color:#EF5354; margin-top:15px">This region is secured</div>
                      </v-col>
                    </v-row>
                  </v-card>
                </v-form>
                <v-divider v-if="regionDialogItem['ssh_tunnel']" style="margin-top:15px"></v-divider>
                <v-row v-if="regionDialogItem['ssh_tunnel']" no-gutters style="margin-top:15px">
                  <v-col>
                    <v-btn :loading="loading" color="info" @click="testRegionConnection()">Test Connection</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- COLUMNS DIALOG -->
    <!-------------------->
    <v-dialog v-model="columnsDialog" max-width="600px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="text-subtitle-1 white--text">FILTER COLUMNS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAllColumns" text title="Select all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAllColumns" text title="Deselect all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="columnsDialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <div class="text-body-1" style="margin-bottom:10px">Select the columns to display:</div>
                  <v-checkbox v-model="columnsRaw" label="Name" value="name" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Region" value="region" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Engine" value="version" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Hostname" value="hostname" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Port" value="port" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Username" value="username" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="SSL" value="ssl" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Group" value="group" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Owner" value="owner" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Usage" value="usage" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created By" value="created_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created At" value="created_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated By" value="updated_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated At" value="updated_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-divider style="margin-top:15px;"></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn @click="filterColumns" :loading="loading" color="#00b16a">Confirm</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="columnsDialog = false" style="margin-left:5px;">Cancel</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- CONFIRM DIALOG -->
    <!-------------------->
    <v-dialog v-model="confirm_dialog" persistent max-width="640px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">CONFIRMATION</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn @click="confirm_dialog = false" icon style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-alert dense color="#EF5354" style="margin-top:15px">This server is being used in some sections.</v-alert>
                <div class="subtitle-1" style="margin-top:10px; margin-bottom:10px;">This server won't be usable in the selected sections. Do you want to proceed?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitServer(false)">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="confirm_dialog = false" style="margin-left:5px">CANCEL</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import axios from 'axios';
import moment from 'moment'

export default {
  data: () => ({
    disabledResources: false,
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Region', align: 'left', value: 'region'},
      { text: 'Engine', align: 'left', value: 'version' },
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'SSL', align: 'left', value: 'ssl' },
      { text: 'Group', align: 'left', value: 'group' },
      { text: 'Owner', align: 'left', value: 'owner' },
      { text: 'Usage', align: 'left', value: 'usage' },
      { text: 'Created By', align: 'left', value: 'created_by' },
      { text: 'Created At', align: 'left', value: 'created_at' },
      { text: 'Updated By', align: 'left', value: 'updated_by' },
      { text: 'Updated At', align: 'left', value: 'updated_at' },
    ],
    servers: [],
    items: [],
    selected: [],
    search: '',
    item: { group_id: null, owner_id: null, name: '', region_id: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, ssl_ca_certificate: null, ssl_client_key: null, ssl_client_certificate: null, ssl_verify_ca: false, client_disabled: false, shared: false, usage: [], secured: false },
    mode: '',
    loading: true,
    engines: {
      'MySQL': ['MySQL 5.6', 'MySQL 5.7', 'MySQL 8.0'],
      'Aurora MySQL': ['Aurora MySQL 5.6', 'Aurora MySQL 5.7', 'Aurora MySQL 8.0']
    },
    versions: [],
    usage: [],
    showPassword: false,
    // Dialog: Item
    dialog: false,
    dialog_title: '',
    users: [],
    // Dialog: Confirm
    confirm_dialog: false,
    // Region Dialog
    regionDialog: false,
    regionDialogItem: {},
    showRegionPassword: false,
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','region','version','hostname','port','username','shared','group','owner','usage'],
    columnsRaw: [],
    // Regions
    regions: [],
  }),
  props: ['tab','groups','filter'],
  mounted() {
    EventBus.$on('get-servers', this.getServers);
    EventBus.$on('filter-servers', this.filterServers);
    EventBus.$on('filter-server-columns', this.filterServerColumns);
    EventBus.$on('new-server', this.newServer);
    EventBus.$on('clone-server', this.cloneServer);
    EventBus.$on('edit-server', this.editServer);
    EventBus.$on('delete-server', this.deleteServer);
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
    ssl_active: function() {
      let elements = []
      if (this.item.ssl_client_key != null) elements.push('Client Key')
      if (this.item.ssl_client_certificate != null) elements.push('Client Certificate')
      if (this.item.ssl_ca_certificate != null) elements.push('CA Certificate')
      return elements.join(' + ')
    }
  },
  methods: {
    personalClick() {
      this.item.shared = false
    },
    sharedClick() {
      this.item.shared = true
    },
    groupChanged() {
      this.item.owner_id = null
      this.item.region_id = null
      this.item.usage = []
      requestAnimationFrame(() => {
        if (!this.item.shared) this.$refs.owner_id.focus()
      })
      if (this.item.group_id != null) {
        this.getRegions()
        this.getUsers()
        this.buildUsage()
      }
    },
    ownerChanged() {
      this.getRegions()
    },
    getUsers() {
      axios.get('/admin/inventory/users', { params: { group_id: this.item.group_id }})
        .then((response) => {
          this.users = response.data.users
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    buildUsage() {
      axios.get('/admin/groups/usage', { params: { group_id: this.item.group_id }})
        .then((response) => {
          const data = response.data.group
          this.usage = []
          if (data['deployments_enabled'] == 1) this.usage.push('Deployments')
          if (data['monitoring_enabled'] == 1) this.usage.push('Monitoring')
          if (data['utils_enabled'] == 1) this.usage.push('Utils')
          if (data['client_enabled'] == 1) this.usage.push('Client')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    getServers() {
      this.loading = true
      const payload = (this.filter.by == 'group' && this.filter.group != null) ? { group_id: this.filter.group } : (this.filter.by == 'user' && this.filter.user != null) ? { user_id: this.filter.user } : {}
      axios.get('/admin/inventory/servers', { params: payload})
        .then((response) => {
          response.data.servers.map(x => {
            x['created_at'] = this.dateFormat(x['created_at'])
            x['updated_at'] = this.dateFormat(x['updated_at'])
          })
          this.servers = response.data.servers
          this.items = response.data.servers
          this.filterBy()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getRegions() {
      if (!this.item.shared && this.item.owner_id == null) return
      const payload = this.item.shared ? { group_id: this.item.group_id } : { group_id: this.item.group_id, owner_id: this.item.owner_id }
      axios.get('/admin/inventory/regions', { params: payload})
        .then((response) => {
          this.regions = response.data.regions.map(x => ({ id: x.id, name: x.name, shared: x.shared }))
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    openRegion(region_id) {
      const payload = { id: region_id }
      axios.get('/admin/inventory/regions', { params: payload})
        .then((response) => {
          const regions = response.data.regions
          if (regions.length == 0) this.notification('This region does not exist', '#EF5354')
          else {
            this.regionDialogItem = regions[0]
            this.regionDialog = true
          }
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    selectEngine(value) {
      if (this.item.port == '') {
        if (['MySQL','Aurora MySQL'].includes(value)) this.item.port = '3306'
        else if (value == 'PostgreSQL') this.item.port = '5432'
      }
      this.versions = this.engines[value]
    },
    newServer() {
      this.mode = 'new'
      this.users = []
      this.regions = []
      this.usage = []
      this.item = { group_id: this.filter.group, owner_id: null, name: '', region_id: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, ssl_ca_certificate: null, ssl_client_key: null, ssl_client_certificate: null, ssl_verify_ca: false, client_disabled: false, shared: false, secured: false, usage: [...this.usage] }
      if (this.filter.group != null) { this.getUsers(); this.getRegions(); this.buildUsage(); }
      this.dialog_title = 'NEW SERVER'
      this.dialog = true
    },
    cloneServer() {
      this.mode = 'clone'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item.usage = this.parseUsage(this.item.usage)
      this.getUsers()
      this.getRegions()
      this.buildUsage()
      this.versions = this.engines[this.item.engine]
      this.dialog_title = 'CLONE SERVER'
      this.dialog = true
    },
    editServer() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item.usage = this.parseUsage(this.item.usage)
      this.getUsers()
      this.getRegions()
      this.buildUsage()
      this.versions = this.engines[this.item.engine]
      this.dialog_title = 'EDIT SERVER'
      this.dialog = true
    },
    deleteServer() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE SERVER'
      this.dialog = true
    },
    submitServer(check=true) {
      this.confirm_dialog = false
      if (['new','clone'].includes(this.mode)) this.newServerSubmit()
      else if (this.mode == 'edit') this.editServerSubmit(check)
      else if (this.mode == 'delete') this.deleteServerSubmit(check)
    },
    async newServerSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get SSL Imported Files
      let ssl_ca_certificate = await this.readFileAsync(this.item.ssl_ca_certificate)
      let ssl_client_key = await this.readFileAsync(this.item.ssl_client_key)
      let ssl_client_certificate = await this.readFileAsync(this.item.ssl_client_certificate)
      if (this.item.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
        this.notification('Import at least one SSL certificate/key', '#EF5354')
        return
      }
      // Parse SSL
      ssl_ca_certificate = (ssl_ca_certificate === undefined) ? null : ssl_ca_certificate
      ssl_client_key = (ssl_client_key === undefined) ? null : ssl_client_key
      ssl_client_certificate = (ssl_client_certificate === undefined) ? null : ssl_client_certificate
      // Add item in the DB
      this.loading = true
      const payload = {...this.item, usage: this.parseUsage(this.item.usage), ssl_ca_certificate, ssl_client_key, ssl_client_certificate}
      axios.post('/admin/inventory/servers', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getServers()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    async editServerSubmit(check) {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get SSL Imported Files
      let ssl_ca_certificate = await this.readFileAsync(this.item.ssl_ca_certificate)
      let ssl_client_key = await this.readFileAsync(this.item.ssl_client_key)
      let ssl_client_certificate = await this.readFileAsync(this.item.ssl_client_certificate)
      if (this.item.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
        this.notification('Import at least one SSL certificate/key', '#EF5354')
        return
      }
      // Parse SSL
      ssl_ca_certificate = (ssl_ca_certificate === undefined) ? null : ssl_ca_certificate
      ssl_client_key = (ssl_client_key === undefined) ? null : ssl_client_key
      ssl_client_certificate = (ssl_client_certificate === undefined) ? null : ssl_client_certificate
      // Edit item in the DB
      this.loading = true
      const payload = {...this.item, usage: this.parseUsage(this.item.usage), check, ssl_ca_certificate, ssl_client_key, ssl_client_certificate}
      axios.put('/admin/inventory/servers', payload)
        .then((response) => {
          if (response.status == 202) this.confirm_dialog = true
          else {
            this.notification(response.data.message, '#00b16a')
            this.getServers()
            this.selected = []
            this.dialog = false
          }
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteServerSubmit(check) {
      this.loading = true
      // Build payload
      const payload = { servers: JSON.stringify(this.selected.map((x) => x.id)), check }
      // Delete items to the DB
      axios.delete('/admin/inventory/servers', { params: payload })
        .then((response) => {
          if (response.status == 202) this.confirm_dialog = true
          else {
            this.notification(response.data.message, '#00b16a')
            this.getServers()
            this.selected = []
            this.dialog = false
          }
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    async testConnection() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get SSL Imported Files
      let ssl_ca_certificate = await this.readFileAsync(this.item.ssl_ca_certificate)
      let ssl_client_key = await this.readFileAsync(this.item.ssl_client_key)
      let ssl_client_certificate = await this.readFileAsync(this.item.ssl_client_certificate)
      if (this.item.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
        this.notification('Import at least one SSL certificate/key', '#EF5354')
        return
      }
      // Test Connection
      this.loading = true
      const payload = {
        region_id: this.item.region_id,
        server: { ...this.item, ssl_client_key, ssl_client_certificate, ssl_ca_certificate, ssl_verify_ca: this.item.ssl_verify_ca }
      }
      axios.post('/admin/inventory/servers/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    async testRegionConnection() {
      // Get SSH Private Key
      let key = await this.readFileAsync(this.regionDialogItem.key)
      // Test Connection
      this.loading = true
      const payload = {...this.regionDialogItem, key}
      axios.post('/admin/inventory/regions/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    generatePassword() {
      axios.get('/inventory/genpass')
        .then((response) => {
          this.item.password = response.data.password
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    filterBy() {
      let servers = JSON.parse(JSON.stringify(this.servers))
      // Filter by scope
      if (this.filter.scope == 'personal') servers = servers.filter(x => !x.shared)
      else if (this.filter.scope == 'shared') servers = servers.filter(x => x.shared)
      // Filter by secured
      if (this.filter.secured == 'secured') servers = servers.filter(x => x.secured)
      else if (this.filter.secured == 'not_secured') servers = servers.filter(x => !x.secured)
      // Init disabled resources
      this.disabledResources = this.items.some(x => !x.active)
      // Assign filter
      this.items = servers
    },
    parseUsage(val) {
      if (typeof val == 'string') {
        let ret = []
        if (val.includes('D')) ret.push('Deployments')
        if (val.includes('M')) ret.push('Monitoring')
        if (val.includes('U')) ret.push('Utils')
        if (val.includes('C')) ret.push('Client')
        return ret
      }
      else {
        let ret = ''
        if (val.includes('Deployments')) ret += 'D'
        if (val.includes('Monitoring')) ret += 'M'
        if (val.includes('Utils')) ret += 'U'
        if (val.includes('Client')) ret += 'C'
        return ret
      }
    },
    filterServers() {
      this.selected = []
      if (this.filter.group != null) this.columns = this.columns.filter(x => x != 'group')
      else if (!this.columns.some(x => x == 'group')) this.columns.push('group')
      this.getServers()
    },
    filterServerColumns() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','region','version','hostname','port','username','shared','group','owner','usage','ssl','created_by','created_at','updated_by','updated_at']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    readFileAsync(file) {
      if (file == null || typeof file !== 'object') return file
      return new Promise((resolve, reject) => {
        let reader = new FileReader()
        reader.onload = () => { resolve(reader.result)}
        reader.onerror = reject
        reader.readAsText(file, 'utf-8')
      })
    },
    removeSSL() {
      this.item.ssl_ca_certificate = null
      this.item.ssl_client_key = null
      this.item.ssl_client_certificate = null
    },
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
    },
    notification(message, color, persistent=false) {
      EventBus.$emit('notification', message, color, persistent)
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      this.showPassword = false
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (this.mode == 'new') {
          if (this.filter.group == null) this.$refs.group_id.focus()
          else this.$refs.name.focus()
        }
        else if (['clone','edit'].includes(this.mode)) this.$refs.name.focus()
      })
    },
    selected(val) {
      EventBus.$emit('change-selected', val)
    },
    tab(val) {
      this.selected = []
      if (val == 0) this.getServers()
    },
    'item.shared': function (newVal, oldVal) {
      if (newVal != oldVal) this.getRegions()
    },
  }
}
</script> 