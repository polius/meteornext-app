<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">QUERIES</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn text title="Define monitoring rules and settings" @click="openSettings()"><v-icon small style="margin-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
          <v-btn text title="Select servers to monitor" @click="openServers()"><v-icon small style="margin-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn text title="Filter queries" @click="filter_dialog = true" :style="{ backgroundColor : filter_applied ? '#4ba2f1' : '' }"><v-icon small style="margin-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn text title="Refresh query list" @click="getQueries()"><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-btn text title="Export queries" @click="exportQueries()"><v-icon small style="margin-right:10px">fas fa-arrow-down</v-icon>EXPORT</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="queries_search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="filterColumnsClick" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table :headers="computedHeaders" :items="queries_items" :options.sync="queries_options" :server-items-length="queries_total" :expanded.sync="expanded" single-expand item-key="id" show-expand :loading="loading" class="elevation-1" style="padding-top:5px;" mobile-breakpoint="0">
        <template v-slot:[`item.first_seen`]="{ item }">
          <span style="display:block; min-width:130px">{{ dateFormat(item.first_seen) }}</span>
        </template>
        <template v-slot:[`item.last_seen`]="{ item }">
          <span style="display:block; min-width:130px">{{ dateFormat(item.last_seen) }}</span>
        </template>
        <template v-slot:[`item.user`]="{ item }">
          <span style="display:block; min-width:44px">{{ item.user }}</span>
        </template>
        <template v-slot:[`item.server`]="{ item }">
          <v-btn @click="getServer(item.server_id)" text class="body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
            <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
            <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
            {{ item.server }}
          </v-btn>
        </template>
        <template v-slot:[`item.host`]="{ item }">
          <span style="display:block; min-width:45px">{{ item.host }}</span>
        </template>
        <template v-slot:[`item.db`]="{ item }">
          <span style="display:block; min-width:70px">{{ item.db }}</span>
        </template>
        <template v-slot:[`item.last_execution_time`]="{ item }">
          <span style="display:block; min-width:62px">{{ item.last_execution_time }}</span>
        </template>
        <template v-slot:[`item.max_execution_time`]="{ item }">
          <span style="display:block; min-width:128px">{{ item.max_execution_time }}</span>
        </template>
        <template v-slot:[`item.avg_execution_time`]="{ item }">
          <span style="display:block; min-width:125px">{{ item.avg_execution_time }}</span>
        </template>
        <template v-slot:[`item.count`]="{ item }">
          <span style="display:block; min-width:52px">{{ item.count }}</span>
        </template>
        <template v-slot:[`item.query_text`]="{ item }">
          <span style="white-space:nowrap">{{ item.query_text }}</span>
        </template>
        <template v-slot:expanded-item="{ headers }">
          <td :colspan="headers.length">
            <div id="editor" style="width:calc(100vw - 70px); margin-top:15px; margin-bottom:15px"></div>
          </td>
        </template>
        <template v-slot:[`footer.prepend`]>
          <div v-if="disabledResources" class="text-body-2 font-weight-regular" style="margin:10px"><v-icon small color="warning" style="margin-right:10px; margin-bottom:2px">fas fa-exclamation-triangle</v-icon>Some servers are disabled. Consider the possibility of upgrading your license.</div>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="settings_dialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-cog</v-icon>SETTINGS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="settings_dialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-text-field filled v-model="settings.query_execution_time" label="Minimum Execution Time (seconds)" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-bottom:10px;" hide-details></v-text-field>
                  <v-text-field filled v-model="settings.query_data_retention" label="Data Retention (days)" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-top:15px; margin-bottom:10px;" hide-details></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitSettings()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="settings_dialog=false" style="margin-left:5px;">CANCEL</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="servers_dialog" max-width="896px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-database</v-icon>SERVERS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="servers_dialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px">
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-text-field v-model="treeviewSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding: 10px;">
                      <div v-if="treeviewItems.length == 0" class="body-2" style="text-align:center">No servers available</div>
                      <v-treeview v-else :active.sync="treeviewSelectedRaw" item-key="id" :items="treeviewItems" :open="treeviewOpenedRaw" :search="treeviewSearch" hoverable open-on-click multiple-active activatable transition>
                        <template v-slot:label="{ item }">
                          <v-icon v-if="item.children" small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EF5354' : 'warning'" :style="item.shared ? 'margin-right:10px; margin-bottom:2px' : 'margin-left:2px; margin-right:16px; margin-bottom:2px'">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:prepend="{ item }">
                          <v-icon v-if="!item.children && !item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon v-if="!item.children" small>fas fa-server</v-icon>
                        </template>
                        <template v-slot:append="{ item }">
                          <v-chip v-if="!item.children" label><v-icon small :color="item.shared ? '#EF5354' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.shared ? 'Shared' : 'Personal' }}</v-chip>
                        </template>
                      </v-treeview>
                    </v-card-text>
                  </v-card>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px">
                  <v-btn :loading="loading" color="#00b16a" @click="submitServers()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="servers_dialog=false" style="margin-left:5px;">CANCEL</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="filter_dialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filter_dialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 10px 15px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:20px;">
                  <v-row>
                    <v-col>
                      <v-autocomplete v-model="filter.server" item-value="id" item-text="name" :items="filterServers" label="Server" style="padding-top:0px;" hide-details>
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" :style="item.shared ? 'margin-right:10px' : 'margin-right:13px; margin-left:3px'">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.host" label="Host" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.hostFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.host === undefined || filter.host.length == 0) || (filter.host.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.user" label="User" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.userFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.user === undefined || filter.user.length == 0) || (filter.user.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.database" label="Database" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.databaseFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.database === undefined || filter.database.length == 0) || (filter.database.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.query" label="Query" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.queryFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.query === undefined || filter.query.length == 0) || (filter.query.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.firstSeenFrom" label="First Seen - From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('firstSeenFrom')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.firstSeenTo" label="First Seen - To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('firstSeenTo')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.lastSeenFrom" label="Last Seen - From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('lastSeenFrom')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.lastSeenTo" label="Last Seen - To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('lastSeenTo')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="cancelFilter()" style="margin-left:5px;">CANCEL</v-btn>
                  <v-btn v-if="filter_applied" :disabled="loading" color="info" @click="clearFilter()" style="float:right;">Remove Filter</v-btn>
                </div>
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
          <v-toolbar-title class="white--text subtitle-1">FILTER COLUMNS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAllColumns" text title="Select all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAllColumns" text title="Deselect all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="columnsDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <div class="text-body-1" style="margin-bottom:10px">Select the columns to display:</div>
                  <v-checkbox v-model="columnsRaw" label="First Seen" value="first_seen" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Last Seen" value="last_seen" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Server" value="server" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Host" value="host" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="User" value="user" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Database" value="db" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Elapsed" value="last_execution_time" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Max Execution Time" value="max_execution_time" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Avg Execution Time" value="avg_execution_time" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Count" value="count" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Query" value="query_text" hide-details style="margin-top:5px"></v-checkbox>
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

    <!-- Preload -->
    <div v-show="false" id="editor" style="height:50vh; width:100%"></div>

    <!------------------->
    <!-- SERVER DIALOG -->
    <!------------------->
    <v-dialog v-model="serverDialog" max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">SERVER</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn readonly title="Create the server only for a user" :color="!server.shared ? 'primary' : '#779ecb'" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn readonly title="Create the server for all users in a group" :color="server.shared ? 'primary' : '#779ecb'"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="serverDialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-progress-linear v-show="serverLoading" indeterminate></v-progress-linear>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="6" style="padding-right:10px">
                      <v-text-field readonly v-model="server.name" label="Name" style="margin-top:0px; padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:10px">
                      <v-text-field readonly v-model="server.region" label="Region" style="margin-top:0px; padding-top:0px" hide-details>
                        <template v-slot:prepend-inner>
                          <v-icon small :color="server.region_shared ? '#EB5F5D' : 'warning'" style="margin-top:4px; margin-right:5px">{{ server.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                        </template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                  <div v-if="!server.secured" style="margin-top:25px">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field readonly v-model="server.engine" label="Engine" style="padding-top:0px"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field readonly v-model="server.version" label="Version" style="padding-top:0px"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field readonly v-model="server.hostname" label="Hostname" style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field readonly v-model="server.port" label="Port" style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field readonly v-model="server.username" label="Username" style="padding-top:0px;"></v-text-field>
                    <v-text-field readonly v-model="server.password" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" style="padding-top:0px;" hide-details></v-text-field>
                  </div>
                  <!-- SSL -->
                  <v-card v-if="server.ssl" style="height:52px; margin-top:15px; margin-bottom:15px">
                    <v-row no-gutters>
                      <v-col cols="auto" style="display:flex; margin:15px">
                        <v-icon color="#00b16a" style="font-size:17px; margin-top:3px">fas fa-key</v-icon>
                      </v-col>
                      <v-col>
                        <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a SSL connection</div>
                      </v-col>
                    </v-row>
                  </v-card>
                  <!-- SSH -->
                  <v-card v-if="server.ssh" style="height:52px; margin-top:15px; margin-bottom:15px">
                    <v-row no-gutters>
                      <v-col cols="auto" style="display:flex; margin:15px">
                        <v-icon color="#2196f3" style="font-size:16px; margin-top:4px">fas fa-terminal</v-icon>
                      </v-col>
                      <v-col>
                        <div class="text-body-1" style="color:#2196f3; margin-top:15px">Using a SSH connection</div>
                      </v-col>
                    </v-row>
                  </v-card>
                  <!-- SECURED -->
                  <v-card v-if="server.secured" style="height:52px; margin-top:15px; margin-bottom:15px">
                  <v-row no-gutters>
                    <v-col cols="auto" style="display:flex; margin:15px">
                      <v-icon color="#EF5354" style="font-size:16px; margin-top:4px">fas fa-lock</v-icon>
                    </v-col>
                    <v-col>
                      <div class="text-body-1" style="color:#EF5354; margin-top:15px">This server is secured</div>
                    </v-col>
                  </v-row>
                </v-card>
                <v-text-field readonly outlined v-model="server.usage" label="Usage" style="margin-top:20px; margin-bottom:15px" hide-details></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:15px">
                  <v-col>
                    <v-btn :loading="serverLoading" color="info" @click="testConnection()">Test Connection</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dateTimeDialog" persistent width="290px">
      <v-date-picker v-if="dateTimeMode == 'date'" v-model="dateTimeValue.date" color="info" scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="dateTimeMode == 'time'" v-model="dateTimeValue.time" color="info" format="24hr" use-seconds scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-time-picker>
    </v-dialog>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<style scoped>
.ace-monokai {
  background-color: #303030;
}
::deep .ace_scroller {
  padding: 13px!important;
}
::deep .ace_scrollbar.ace_scrollbar-v {
  display: none;
}
</style>

<script>
import axios from 'axios'
import moment from 'moment'
import ace from 'ace-builds'
import 'ace-builds/webpack-resolver'
import 'ace-builds/src-noconflict/ext-language_tools'
import sqlFormatter from '@sqltools/formatter'

export default {
  data: () => ({
    disabledResources: false,
    loading: true,

    // Queries
    queries_headers: [
      { text: 'First Seen', align: 'left', value: 'first_seen' },
      { text: 'Last Seen', align: 'left', value: 'last_seen' },
      { text: 'Server', align: 'left', value: 'server' },
      { text: 'Host', align: 'left', value: 'host' },
      { text: 'User', align: 'left', value: 'user' },
      { text: 'Database', align: 'left', value: 'db' },
      { text: 'Elapsed', align: 'left', value: 'last_execution_time' },
      { text: 'Max Execution Time', align: 'left', value: 'max_execution_time' },
      { text: 'Avg Execution Time', align: 'left', value: 'avg_execution_time' },
      { text: 'Count', align: 'left', value: 'count' },
      { text: 'Query', align: 'left', value: 'query_text', sortable: false },
    ],
    queries_origin: [],
    queries_items: [],
    queries_search: '',
    queries_total: 0,
    queries_options: {},
    editor: null,
    expanded: [],

    // Settings Dialog
    settings_dialog: false,        
    settings: { query_execution_time: '10', query_data_retention: '24' },
    execution_time: '10',
    data_retention: '24',

    // Servers Dialog
    servers_dialog: false,
    treeviewItems: [],
    treeviewSelected: [],
    treeviewSelectedRaw: [],
    treeviewOpened: [],
    treeviewOpenedRaw: [],
    treeviewSearch: '',
    submit_servers: true,

    // Filter Dialog
    filter_dialog: false,
    filter: {},
    filters: [
      {id: 'equal', name: 'Equal'},
      {id: 'not_equal', name: 'Not equal'},
      {id: 'starts', name: 'Starts'},
      {id: 'not_starts', name: 'Not starts'},
      {id: 'contains', name: 'Contains'},
      {id: 'not_contains', name: 'Not contains'}
    ],
    filterServers: [],
    filter_applied: false,

    // DateTime Dialog
    dateTimeDialog: false,
    dateTimeMode: 'date',
    dateTimeField: '',
    dateTimeValue: { date: null, time: null },

    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['query_text','db','server','last_seen','last_execution_time','count'],
    columnsRaw: [],

    // Server Dialog
    serverLoading: false,
    serverDialog: false,
    server: {},
    showPassword: false,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  computed: {
    computedHeaders() { return this.queries_headers.filter(x => this.columns.includes(x.value)) }
  },
  mounted() {
    this.editor = ace.edit("editor", {
      mode: "ace/mode/mysql",
      theme: "ace/theme/monokai",
      keyboardHandler: "ace/keyboard/vscode",
    })
  },
  methods: {
    getQueries() {
      this.loading = true
      const { sortBy, sortDesc, page, itemsPerPage } = this.queries_options
      var payload = {}
      // Build Filter
      let filter = this.filter_applied ? JSON.parse(JSON.stringify(this.filter)) : null
      if (this.filter_applied && 'firstSeenFrom' in filter && this.dateValid(this.filter.firstSeenFrom)) filter.firstSeenFrom = this.dateUTC(this.filter.firstSeenFrom)
      if (this.filter_applied && 'firstSeenTo' in filter && this.dateValid(this.filter.firstSeenTo)) filter.firstSeenTo = this.dateUTC(this.filter.firstSeenTo)
      if (this.filter_applied && 'lastSeenFrom' in filter && this.dateValid(this.filter.lastSeenFrom)) filter.lastSeenFrom = this.dateUTC(this.filter.lastSeenFrom)
      if (this.filter_applied && 'lastSeenTo' in filter && this.dateValid(this.filter.lastSeenTo)) filter.lastSeenTo = this.dateUTC(this.filter.lastSeenTo)
      if (filter != null) payload['filter'] = filter
      // Build sort
      if (sortBy.length > 0) payload['sort'] = { column: sortBy[0], desc: sortDesc[0] }
      // Get queries
      axios.get('/monitoring/queries', { params: payload})
        .then((response) => {
          // First time
          if (this.submit_servers) {
            this.parseSettings(response.data.settings)
            this.parseTreeView(response.data.servers)
            this.parseServers(response.data.servers)
            this.submit_servers = false
          }
          let items = response.data.queries
          this.queries_total = items.length
          if (itemsPerPage > 0) items = items.slice((page - 1) * itemsPerPage, page * itemsPerPage)
          this.queries_origin = items
          this.queries_items = items
          // Apply search
          this.applySearch(this.queries_search)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    parseSettings(settings) {
      if (settings.length > 0) {
        this.settings.query_execution_time = this.execution_time = settings[0]['query_execution_time']
        this.settings.query_data_retention = this.data_retention = settings[0]['query_data_retention']
      }
    },
    parseTreeView(servers) {
      var data = []
      var selected = []
      var opened = []
      if (servers.length == 0) return data

      // Parse Servers
      for (let i = 0; i < servers.length; ++i) {
        let index = data.findIndex(x => x.id == 'r' + servers[i]['region_id'])
        if (index == -1) data.push({ id: 'r' + servers[i]['region_id'], name: servers[i]['region_name'], shared: servers[i]['region_shared'], children: [{ id: servers[i]['server_id'], name: servers[i]['server_name'], shared: servers[i]['server_shared'], active: servers[i]['server_active'] }] })
        else data[index]['children'].push({ id: servers[i]['server_id'], name: servers[i]['server_name'], shared: servers[i]['server_shared'], active: servers[i]['server_active']})

        // Check selected
        if (servers[i]['selected']) {
          selected.push(servers[i]['server_id'])
          opened.push('r' + servers[i]['region_id'])
        }
      }
      if (!this.servers_dialog) {
        this.treeviewItems = data
        this.treeviewSelected = selected
        this.treeviewOpened = opened
      }
      this.disabledResources = servers.some(x => x.selected && !x.server_active)
    },
    parseServers(servers) {
      const serversList = servers.map(x => ({id: x.server_id, name: x.server_name, shared: x.server_shared}))
      this.filterServers = serversList.sort((a,b) => (a.name.toLowerCase() > b.name.toLowerCase()) ? 1 : ((b.name.toLowerCase() > a.name.toLowerCase()) ? -1 : 0))
    },
    openSettings() {
      this.settings = { query_execution_time: this.execution_time, query_data_retention: this.data_retention },
      this.settings_dialog = true
    },
    submitSettings() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Update settings        
      this.loading = true
      this.settings.monitor_base_url = window.location.origin
      const payload = this.settings
      axios.put('/monitoring/settings', payload)
        .then((response) => {
          this.execution_time = this.settings.query_execution_time
          this.data_retention = this.settings.query_data_retention
          this.notification(response.data.message, '#00b16a')
          this.settings_dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    cancelFilter() {
      if (!this.filter_applied) this.filter = {}
      this.filter_dialog = false
    },
    openServers() {
      this.treeviewSelectedRaw = JSON.parse(JSON.stringify(this.treeviewSelected))
      this.treeviewOpenedRaw = JSON.parse(JSON.stringify(this.treeviewOpened))
      this.treeviewSearch = ''
      this.servers_dialog = true
    },
    submitServers() {
      this.loading = true
      const payload = this.treeviewSelectedRaw
      axios.put('/monitoring/queries', payload)
        .then((response) => {
          this.treeviewSelected = JSON.parse(JSON.stringify(this.treeviewSelectedRaw))
          this.treeviewOpened = JSON.parse(JSON.stringify(this.treeviewOpenedRaw))
          this.notification(response.data.message, '#00b16a')
          this.servers_dialog = false
          this.submit_servers = true
          this.getQueries()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    getServer(server_id) {
      // Get Server
      this.serverLoading = true
      this.showPassword = false
      this.serverDialog = true
      const payload = { server_id: server_id }
      axios.get('/inventory/servers', { params: payload })
        .then((response) => {
          // Build usage
          let usage = []
          if (response.data.data[0].usage.includes('D')) usage.push('Deployments')
          if (response.data.data[0].usage.includes('M')) usage.push('Monitoring')
          if (response.data.data[0].usage.includes('U')) usage.push('Utils')
          if (response.data.data[0].usage.includes('C')) usage.push('Client')
          // Add server
          this.server = {...response.data.data[0], usage: usage.join(', ')}
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.serverLoading = false)
    },
    testConnection() {
      // Test Connection
      this.notification('Testing Server...', 'info')
      this.serverLoading = true
      const payload = {
        region: this.server.region_id,
        server: this.server.id
      }
      axios.post('/inventory/servers/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.serverLoading = false)
    },
    submitFilter() {
      this.loading = true
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      // Apply filter
      this.filter_applied = true
      this.getQueries()
      this.filter_dialog = false
    },
    clearFilter() {
      this.loading = true
      this.filter = {}
      this.filter_applied = false
      this.getQueries()
      this.filter_dialog = false
    },
    applySearch(newValue) {
      if (newValue.length == 0) this.queries_items = this.queries_origin.slice(0)
      else {
        let items = []
        for (let i in this.queries_origin) {
          let keys = Object.keys(this.queries_origin[i])
          for (let k in keys) {
            if (this.queries_origin[i][keys[k]].toString().includes(newValue)) { items.push(this.queries_origin[i]); break; }
          }
        }
        this.queries_items = items
      }
    },
    exportQueries() {
      let replacer = (key, value) => value === null ? undefined : value
      let header = this.computedHeaders.map(x => x.value)
      let exportData = this.queries_items.map(row => header.map(fieldName => {
        if (['first_seen','last_seen'].includes(fieldName)) return moment(row[fieldName]).format("YYYY-MM-DD HH:mm:ss") + ' UTC'
        else return JSON.stringify(row[fieldName], replacer)
      }).join(','))
      exportData.unshift(this.computedHeaders.map(row => row['text']).join(','))
      exportData = exportData.join('\r\n')
      this.download('queries.csv', exportData)
    },
    download(filename, text) {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(new Blob([text]))
      a.setAttribute('download', filename)
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },
    dateTimeDialogOpen(field) {
      this.dateTimeField = field
      this.dateTimeMode = 'date'
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
      if (this.filter[field] !== undefined && this.filter[field].length > 0) {
        let isValid = moment(this.filter[field], 'YYYY-MM-DD HH:mm', true).isValid()
        if (!isValid) {
          this.notification("Enter a valid date", '#EF5354')
          return
        }
        this.dateTimeValue = { date: moment(this.filter[field]).format("YYYY-MM-DD"), time: moment(this.filter[field]).format("HH:mm") }
      }
      this.dateTimeDialog = true
    },
    dateTimeSubmit() {
      if (this.dateTimeMode == 'date') this.dateTimeMode = 'time'
      else {
        this.filter[this.dateTimeField] = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        this.dateTimeDialog = false
      }
    },
    dateTimeNow() {
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
    },
    filterColumnsClick() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    selectAllColumns() {
      this.columnsRaw = ['query_text','db','server','user','host','first_seen','last_seen','last_execution_time','max_execution_time','avg_execution_time','count']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    dateValid(date) {
      return moment(date, 'YYYY-MM-DD HH:mm', true).isValid()
    },
    dateUTC(date) {
      return moment(date).utc().format("YYYY-MM-DD HH:mm:ss")
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    queries_options: {
      handler () { this.getQueries() },
      deep: true
    },
    // eslint-disable-next-line
    queries_search: function (newValue, oldValue) {
      this.applySearch(newValue)
    },
    expanded: function(val) {
      if (val.length == 0) return
      this.$nextTick(() => {
        // Init ACE Editor
        this.editor = ace.edit("editor", {
          mode: "ace/mode/mysql",
          theme: "ace/theme/monokai",
          keyboardHandler: "ace/keyboard/vscode",
          maxLines: 20,
          fontSize: 14,
          showPrintMargin: false,
          // wrap: false,
          readOnly: true,
          showGutter: false,
        })
        this.editor.commands.removeCommand('showSettingsMenu')
        this.editor.container.addEventListener("keydown", (e) => {
          // - Increase Font Size -
          if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
            let size = parseInt(this.editor.getFontSize(), 10) || 12
            this.editor.setFontSize(size + 1)
            e.preventDefault()
          }
          // - Decrease Font Size -
          else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
            let size = parseInt(this.editor.getFontSize(), 10) || 12
            this.editor.setFontSize(Math.max(size - 1 || 1))
            e.preventDefault()
          }
        }, false)
        let sqlFormatted = sqlFormatter.format(this.expanded[0].query_text, { reservedWordCase: 'upper', linesBetweenQueries: 2 })
        this.editor.setValue(sqlFormatted, -1)
      })
    }
  }
}
</script>