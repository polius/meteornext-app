<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">SERVERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn text @click="newServer()"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1 || selected[0].secured == 1" text @click="editServer()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn :disabled="selected.length != 1 || selected[0].secured == 1" @click="cloneServer()" text><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn :disabled="selected.length == 0 || selected.some(x => x.secured) || (!owner && selected.some(x => x.shared))" text @click="deleteServer()"><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="testServer" :disabled="selected.length != 1" title="Test a server connection" text><v-icon small style="margin-right:10px">fas fa-server</v-icon>TEST</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2" @click="filterBy('all')" :style="filter == 'all' ? 'font-weight:600' : 'font-weight:400'">ALL</v-btn>
          <v-btn text class="body-2" @click="filterBy('personal')" :style="filter == 'personal' ? 'font-weight:600' : 'font-weight:400'">PERSONAL</v-btn>
          <v-btn text class="body-2" @click="filterBy('shared')" :style="filter == 'shared' ? 'font-weight:600' : 'font-weight:400'">SHARED</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="openColumnsDialog" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
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
    </v-card>
    <!------------------->
    <!-- SERVER DIALOG -->
    <!------------------->
    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" :disabled="(item.shared == 1 && !owner)" @click="item.shared = false" title="Create the server only for you" :color="!item.shared ? 'primary' : '#779ecb'" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" :disabled="(item.shared == 0 && !owner)" @click="item.shared = true" title="Create the server for all users in your group" :color="item.shared ? 'primary' : '#779ecb'"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-alert v-if="mode != 'delete' && !owner && item.shared" color="warning" outlined dense style="margin-bottom:30px"><v-icon color="warning" style="font-size:16px; margin-bottom:3px; margin-right:10px">fas fa-exclamation-triangle</v-icon>This resource cannot be edited. You are not a group owner.</v-alert>
                <v-form v-if="mode != 'delete'" ref="form" style="margin-top:15px; margin-bottom:15px">
                  <v-row no-gutters style="margin-top:15px">
                    <v-col cols="6" style="padding-right:10px">
                      <v-text-field ref="field" v-model="item.name" :readonly="readonly" :rules="[v => !!v || '']" label="Name" required style="padding-top:0px; margin-top:0px"></v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:10px">
                      <v-autocomplete v-model="item.region_id" item-value="id" item-text="name" :readonly="readonly" :rules="[v => !!v || '']" :items="regions" label="Region" required style="padding-top:0px; margin-top:0px">
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-select v-model="item.engine" :readonly="readonly" :items="Object.keys(engines)" label="Engine" :rules="[v => !!v || '']" required style="padding-top:0px;" v-on:change="selectEngine"></v-select>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-select v-model="item.version" :readonly="readonly" :items="versions" label="Version" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                    </v-col>
                  </v-row>
                  <div style="margin-bottom:15px">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field v-model="item.hostname" :readonly="readonly" :rules="[v => !!v || '']" label="Hostname" required style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field v-model="item.port" :readonly="readonly" :rules="[v => v == parseInt(v) || '']" label="Port" required style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :readonly="readonly" :rules="[v => !!v || '']" label="Username" required autocomplete="username" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" :readonly="readonly" label="Password" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" style="padding-top:0px;" hide-details>
                      <template v-slot:[`append`]>
                        <v-btn title="Generate password" @click="generatePassword" icon><v-icon>mdi-key</v-icon></v-btn>
                        <v-btn :title="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword" icon><v-icon>{{ showPassword ? 'mdi-eye' : 'mdi-eye-off' }}</v-icon></v-btn>
                      </template>
                    </v-text-field>
                    <!-- SSL -->
                    <div v-if="(item.ssl_client_key == null || typeof item.ssl_client_key === 'object') && (item.ssl_client_certificate == null || typeof item.ssl_client_certificate === 'object') && (item.ssl_ca_certificate == null || typeof item.ssl_ca_certificate === 'object')">
                      <v-switch v-model="item.ssl" :readonly="readonly" flat label="SSL Connection" hide-details style="margin-top:20px"></v-switch>
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
                          <v-btn v-if="!readonly" @click="removeSSL" icon title="Remove SSL connection" style="margin:8px"><v-icon style="font-size:18px">fas fa-times</v-icon></v-btn>
                        </v-col>
                      </v-row>
                    </v-card>
                    <!-- <v-checkbox v-if="item.ssl" :readonly="readonly" v-model="item.ssl_verify_ca" label="Verify server certificate against CA" hide-details></v-checkbox> -->
                    <v-select outlined v-model="item.usage" :items="usage" :readonly="readonly" :menu-props="{ top: true, offsetY: true }" label="Usage" multiple hide-details style="margin-top:20px"></v-select>
                  </div>
                </v-form>
                <div v-else>
                  <div class="subtitle-1">Are you sure you want to delete the selected servers?</div>
                  <v-card style="margin-top:15px; margin-bottom:15px">
                    <v-list>
                      <v-list-item v-for="item in selected" :key="item.id" style="min-height:35px">
                        <v-list-item-content style="padding:0px">
                          <v-list-item-title>
                            <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                            <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                            <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                            {{ item.name }}
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                  </v-card>
                  <v-checkbox v-model="dialogConfirm" label="I confirm I want to delete the selected servers." hide-details class="body-1" style="margin-bottom:15px"></v-checkbox>
                </div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:15px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :disabled="mode == 'delete' && !dialogConfirm" :loading="loading" color="#00b16a" @click="submitServer()">CONFIRM</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="testConnection(true)">Test Connection</v-btn>
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
                  <div v-if="!regionDialogItem.secured && regionDialogItem.ssh_tunnel" style="margin-top:25px">
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
                  <v-card v-if="!regionDialogItem.secured && regionDialogItem.key" style="height:52px; margin-top:15px">
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
                  <v-checkbox v-model="columnsRaw" label="Usage" value="usage" hide-details style="margin-top:5px"></v-checkbox>
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
                <v-alert dense color="#EF5354" style="margin-top:15px">This server is currently being used in some sections</v-alert>
                <div class="subtitle-1" style="margin-top:10px; margin-bottom:10px;">Are you sure you want to proceed?</div>
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
    <!-------------->
    <!-- SNACKBAR -->
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
    disabledResources: false,
    filter: 'all',
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Region', align: 'left', value: 'region'},
      { text: 'Engine', align: 'left', value: 'version' },
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'SSL', align: 'left', value: 'ssl'},
      { text: 'Usage', align: 'left', value: 'usage' },
    ],
    servers: [],
    items: [],
    selected: [],
    search: '',
    item: { name: '', region_id: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, ssl_ca_certificate: null, ssl_client_key: null, ssl_client_certificate: null, ssl_verify_ca: false, client_disabled: false, shared: false, usage: [] },
    mode: '',
    loading: true,
    engines: {
      'MySQL': ['MySQL 5.6', 'MySQL 5.7', 'MySQL 8.0'],
      'Amazon Aurora (MySQL)': ['Aurora MySQL 1 (5.6)', 'Aurora MySQL 2 (5.7)', 'Aurora MySQL 3 (8.0)']
    },
    versions: [],
    usage: [],
    showPassword: false,
    // Dialog: Item
    dialog: false,
    dialog_title: '',
    dialogConfirm: false,
    // Regions
    regions: [],
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','region','version','hostname','port','username','shared','usage'],
    columnsRaw: [],
    // Dialog: Confirm
    confirm_dialog: false,
    // Region Dialog
    regionDialog: false,
    regionDialogItem: {},
    showRegionPassword: false,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    readonly: function() { return this.item.shared == 1 && !this.owner },
    deployments_enabled: function() { return this.$store.getters['app/deployments_enabled'] },
    monitoring_enabled: function() { return this.$store.getters['app/monitoring_enabled'] },
    utils_enabled: function() { return this.$store.getters['app/utils_enabled'] },
    client_enabled: function() { return this.$store.getters['app/client_enabled'] },
    ssl_active: function() {
      let elements = []
      if (this.item.ssl_client_key != null) elements.push('Client Key')
      if (this.item.ssl_client_certificate != null) elements.push('Client Certificate')
      if (this.item.ssl_ca_certificate != null) elements.push('CA Certificate')
      return elements.join(' + ')
    },
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  created() {
    this.buildUsage()
    this.getServers()
    this.getRegions()
  },
  methods: {
    buildUsage() {
      if (this.deployments_enabled) this.usage.push('Deployments')
      if (this.monitoring_enabled) this.usage.push('Monitoring')
      if (this.utils_enabled) this.usage.push('Utils')
      if (this.client_enabled) this.usage.push('Client')
    },
    getServers() {
      this.loading = true
      axios.get('/inventory/servers')
        .then((response) => {
          this.servers = response.data.data
          this.items = response.data.data
          this.filterBy(this.filter)
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getRegions() {
      axios.get('/inventory/regions')
        .then((response) => {
          this.regions = response.data.data
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    openRegion(region_id) {
      this.regionDialogItem = this.regions.find(x => x.id == region_id)
      this.regionDialog = true
    },
    selectEngine(value) {
      if (this.item.port == '') {
        if (['MySQL','Amazon Aurora (MySQL)'].includes(value)) this.item.port = '3306'
        else if (value == 'PostgreSQL') this.item.port = '5432'
      }
      this.versions = this.engines[value]
    },
    newServer() {
      this.mode = 'new'
      this.item = { name: '', region_id: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, ssl_ca_certificate: null, ssl_client_key: null, ssl_client_certificate: null, ssl_verify_ca: false, client_disabled: false, shared: false, usage: [...this.usage] }
      this.dialog_title = 'NEW SERVER'
      this.dialog = true
    },
    cloneServer() {
      this.mode = 'clone'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item.usage = this.parseUsage(this.item.usage)
      this.item.shared = (!this.owner) ? false : this.item.shared
      this.versions = this.engines[this.item.engine]
      this.dialog_title = 'CLONE SERVER'
      this.dialog = true
    },
    editServer() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item.usage = this.parseUsage(this.item.usage)
      this.versions = this.engines[this.item.engine]
      this.dialog_title = 'EDIT SERVER'
      this.dialog = true
    },
    deleteServer() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE SERVERS'
      this.dialogConfirm = false
      this.selected.sort((a, b) => a.name.localeCompare(b.name))
      this.dialog = true
    },
    testServer() {
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.testConnection(false)
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
      // Check SSL fields
      if (this.item.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
        this.notification('Import at least one SSL certificate/key', '#EF5354')
        return
      }
      // Add item in the DB
      this.loading = true
      const payload = {...this.item, usage: this.parseUsage(this.item.usage), ssl_ca_certificate, ssl_client_key, ssl_client_certificate}
      axios.post('/inventory/servers', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getServers()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
      // Edit item in the DB
      this.loading = true
      const payload = {...this.item, usage: this.parseUsage(this.item.usage), check, ssl_ca_certificate, ssl_client_key, ssl_client_certificate}
      axios.put('/inventory/servers', payload)
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteServerSubmit(check) {
      this.loading = true
      // Build payload
      const payload = { servers: JSON.stringify(this.selected.map((x) => x.id)), check }
      // Delete items to the DB
      axios.delete('/inventory/servers', { params: payload })
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    async testConnection(check) {
      // Check if all fields are filled
      if (check && this.$refs.form !== undefined && !this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get SSL Imported Files
      let ssl_ca_certificate = await this.readFileAsync(this.item.ssl_ca_certificate)
      let ssl_client_key = await this.readFileAsync(this.item.ssl_client_key)
      let ssl_client_certificate = await this.readFileAsync(this.item.ssl_client_certificate)
      if (!this.item.secured && this.item.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
        this.notification('Import at least one SSL certificate/key', '#EF5354')
        return
      }
      // Test Connection
      this.loading = true
      const payload = {
        region: this.item.region_id,
        server: this.item.secured ? this.item.id : { id: this.item.id, engine: this.item.engine, hostname: this.item.hostname, port: this.item.port, username: this.item.username, password: this.item.password, ssl: this.item.ssl, ssl_client_key, ssl_client_certificate, ssl_ca_certificate, ssl_verify_ca: this.item.ssl_verify_ca }
      }
      axios.post('/inventory/servers/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    testRegionConnection() {
      this.loading = true
      const payload = { region: this.regionDialogItem.id }
      axios.post('/inventory/regions/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    filterBy(val) {
      this.filter = val
      if (val == 'all') this.items = this.servers.slice(0)
      else if (val == 'personal') this.items = this.servers.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.servers.filter(x => x.shared)
      this.disabledResources = this.items.some(x => !x.active)
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
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','region','version','hostname','port','username','ssl','shared','usage']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
    },
    notification(message, color, persistent=false) {
      this.snackbar = false
      setTimeout(() => {
        this.snackbarText = message
        this.snackbarColor = color
        this.snackbarTimeout = persistent ? Number(0) : Number(3000)
        this.snackbar = true
      }, 10)
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      this.showPassword = false
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.field !== 'undefined' && !this.readonly) this.$refs.field.focus()
      })
    },
    regionDialog (val) {
      if (val) this.showRegionPassword = false
    },
  }
}
</script> 