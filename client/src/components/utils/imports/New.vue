<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-plus</v-icon>NEW IMPORT</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="goBack"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-container fluid grid-list-lg style="padding:0px; margin-bottom:10px">
        <v-layout row wrap>
          <v-flex xs12 style="padding-bottom:0px">
            <v-stepper v-model="stepper" vertical style="padding-bottom:10px; background-color:#424242">
              <v-stepper-step :complete="stepper > 1" step="1">SOURCE</v-stepper-step>
              <v-stepper-content step="1" style="padding-top:0px; padding-left:10px">
                <v-card style="margin:5px">
                  <v-card-text>
                    <v-form ref="sourceForm" @submit.prevent>
                      <div class="text-body-1">Choose an import method:</div>
                      <v-radio-group :readonly="loading || (scanID != null && !(['SUCCESS','FAILED','STOPPED'].includes(scanStatus)))" v-model="mode" style="margin-top:10px; margin-bottom:15px" hide-details>
                        <v-radio value="file">
                          <template v-slot:label>
                            <v-icon small color="#23cba7" style="margin-left:7px; margin-right:15px">fas fa-file</v-icon>
                            File
                          </template>
                        </v-radio>
                        <v-radio value="url">
                          <template v-slot:label>
                            <v-icon small color="#ff9800" style="margin-left:6px; margin-right:12px">fas fa-link</v-icon>
                            URL
                          </template>
                        </v-radio>
                        <v-radio value="cloud">
                          <template v-slot:label>
                            <v-icon color="#19b5fe" style="font-size:18px; margin-left:3px; margin-right:8px">fas fa-cloud</v-icon>
                            Cloud
                          </template>
                        </v-radio>
                      </v-radio-group>
                      <v-card>
                        <v-row no-gutters align="center" justify="center">
                          <v-col cols="auto" style="display:flex; margin:15px">
                            <v-icon size="20" color="info">fas fa-info-circle</v-icon>
                          </v-col>
                          <v-col>
                            <div class="text-body-1" style="color:#e2e2e2">Accepted formats: .sql, .gz, .tar, .tar.gz</div>
                          </v-col>
                        </v-row>
                      </v-card>
                      <div v-if="mode == 'file'" style="margin-top:15px">
                        <v-card>
                          <v-row no-gutters align="center" justify="center">
                            <v-col cols="auto" style="display:flex; margin:15px">
                              <v-icon size="18" color="#ff9900" style="margin-bottom:2px">fas fa-star</v-icon>
                            </v-col>
                            <v-col>
                              <div class="text-body-1" style="color:#e2e2e2">Compress your .sql files into .gz to speedup the import process.</div>
                            </v-col>
                          </v-row>
                        </v-card>
                        <v-file-input filled v-model="fileObject" label="File" accept=".sql,.tar,.gz" :rules="[v => !!v || '']" prepend-icon truncate-length="1000" hide-details style="margin-top:15px"></v-file-input>
                      </div>
                      <div v-else-if="mode == 'url'" style="margin-top:15px">
                        <v-text-field filled @keyup.enter="scanFile" :readonly="scanStatus == 'IN PROGRESS'" v-model="source" label="URL" :rules="[v => this.validURL(v) || '' ]" hide-details style="margin-top:15px"></v-text-field>
                        <v-select filled v-model="format" :items="['.sql','.gz','.tar','.tar.gz']" label="Format" required  :rules="[v => !!v || '']" hide-details style="margin-top:15px"></v-select>
                      </div>
                      <div v-else-if="mode == 'cloud'" style="margin-top:15px">
                        <!-- CLOUD KEYS -->
                        <div v-if="cloudPath.length == 1">
                          <div class="subtitle-1 white--text" style="margin-bottom:15px">CLOUD KEYS</div>
                          <v-toolbar dense flat color="#2e3131" style="border-top-left-radius:5px; border-top-right-radius:5px;">
                            <v-text-field v-model="cloudKeysSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                          </v-toolbar>
                          <v-data-table :headers="cloudKeysHeaders" :items="cloudKeysItems" :search="cloudKeysSearch" :loading="loading" loading-text="Loading... Please wait" item-key="id" single-select class="elevation-1" mobile-breakpoint="0">
                            <template v-slot:item="{ item }">
                              <tr>
                                <td v-for="header in cloudKeysHeaders" :key="header.value" @click="cloudKeysClick(item)" style="cursor:pointer">
                                  <div v-if="header.value == 'type'">
                                    <v-icon v-if="item.type == 'aws'" size="22" color="#e47911" title="Amazon Web Services">fab fa-aws</v-icon>
                                    <v-icon v-else-if="item.type == 'google'" size="20" color="#4285F4" title="Google Cloud" style="margin-left:4px">fab fa-google</v-icon>
                                  </div>
                                  <div v-else-if="header.value == 'shared'">
                                    <v-icon v-if="!item.shared" small title="Personal" color="warning" style="margin-right:6px; margin-bottom:2px">fas fa-user</v-icon>
                                    <v-icon v-else small title="Shared" color="#EB5F5D" style="margin-right:6px; margin-bottom:2px">fas fa-users</v-icon>
                                    {{ !item.shared ? 'Personal' : 'Shared' }}
                                  </div>
                                  <div v-else>
                                    {{ item[header.value] }}
                                  </div>
                                </td>
                              </tr>
                            </template>
                          </v-data-table>
                        </div>
                        <div v-else>
                          <!-- BREADCRUMB -->
                          <div class="subtitle-1 white--text" style="margin-top:15px; margin-bottom:15px">{{ cloudPath.length == 2 ? 'BUCKETS' : 'OBJECTS' }}</div>
                          <div class="text-body-1" style="margin-top:15px; margin-bottom:15px">
                            <span v-for="(item, index) in cloudPath" :key="index">
                              <v-icon size="14" v-if="index != 0" style="margin-bottom:1px; margin-right:10px">fas fa-chevron-right</v-icon>
                              <span @click="cloudPathClick(item, index)" :style="`margin-right:10px; ${index < cloudPath.length - 1 ? 'color:#2196f3; cursor:pointer' : ''}`">{{ item }}</span>
                            </span>
                          </div>
                          <!-- BUCKETS -->
                          <v-card v-if="cloudPath.length == 2">
                            <v-card-text style="padding:0px">
                              <v-toolbar dense flat color="#2e3131" style="border-top-left-radius:5px; border-top-right-radius:5px;">
                                <v-text-field v-model="awsBucketsSearch" append-icon="search" label="Find buckets by name" color="white" single-line hide-details></v-text-field>
                              </v-toolbar>
                              <v-data-table v-model="awsBucketsSelected" :headers="awsBucketsHeaders" :items="awsBucketsItems" :search="awsBucketsSearch" :loading="loading" loading-text="Loading... Please wait" item-key="name" single-select class="elevation-1" mobile-breakpoint="0">
                                <template v-slot:item="{ item }">
                                  <tr :style="awsBucketsSelected.length > 0 && awsBucketsSelected[0].name == item.name ? 'background-color:#505050' : ''">
                                    <td v-for="header in awsBucketsHeaders" :key="header.value" @click="awsBucketsClick(item)" style="cursor:pointer">
                                      {{ item[header.value] }}
                                    </td>
                                  </tr>
                                </template>
                              </v-data-table>
                            </v-card-text>
                          </v-card>
                          <!-- OBJECTS -->
                          <div v-else>
                            <v-card>
                              <v-card-text style="padding:0px">
                                <v-toolbar dense flat color="#2e3131" style="border-top-left-radius:5px; border-top-right-radius:5px;">
                                  <v-text-field @keyup="getAWSObjects(true, $event)" v-model="awsObjectsSearch" append-icon="search" label="Find objects by prefix" color="white" single-line hide-details></v-text-field>
                                </v-toolbar>
                                <v-data-table v-model="awsObjectsSelected" :headers="awsObjectsHeaders" :items="awsObjectsItems" :loading="loading" loading-text="Loading... Please wait" item-key="name" single-select class="elevation-1" mobile-breakpoint="0">
                                  <template v-slot:item="{ item }">
                                    <tr :style="awsObjectsSelected.length > 0 && awsObjectsSelected[0].name == item.name ? 'background-color:#505050' : ''">
                                      <td v-for="header in awsObjectsHeaders" :key="header.value" @click="awsObjectsClick(item)" :style="loading || (scanID != null && !(['SUCCESS','FAILED','STOPPED'].includes(scanStatus))) ? 'cursor:not-allowed' : 'cursor:pointer'">
                                        <span v-if="header.value == 'name'">
                                          <v-icon size="16" :color="item['name'].endsWith('/') ? '#e47911' : '#23cba7'" style="margin-right:10px; margin-bottom:2px">{{ item['name'].endsWith('/') ? 'fas fa-folder' : 'far fa-file'}}</v-icon>
                                          {{ item.name }}
                                        </span>
                                        <span v-else-if="header.value == 'type'">
                                          {{ item['name'].endsWith('/') ? 'Folder' : item['name'].indexOf('.') == '-1' ? '-' : item['name'].substring(item['name'].lastIndexOf(".") + 1) }}
                                        </span>
                                        <span v-else-if="header.value == 'size'">
                                          {{ formatBytes(item.size) }}
                                        </span>
                                        <span v-else>{{ item[header.value] }}</span>
                                      </td>
                                    </tr>
                                  </template>
                                </v-data-table>
                              </v-card-text>
                            </v-card>
                          </div>
                        </div>
                      </div>
                      <!--  SIZE -->
                      <div v-if="(size != null) || (mode == 'url' && scanID != null)" class="text-body-1" style="margin-top:20px">File Size: <span class="white--text" style="font-weight:500">{{ formatBytes(size) }}</span></div>
                      <!-- SCAN -->
                      <div v-if="scanID != null" style="margin-top:15px">
                        <div class="subtitle-1 white--text" style="margin-top:10px; margin-bottom:10px">SCAN</div>
                        <div v-if="scanStatus == 'IN PROGRESS'" class="text-body-1"><v-icon title="In Progress" small style="color: #ff9800; margin-right:10px">fas fa-spinner</v-icon>Scanning source file. Please wait...</div>
                        <div v-else-if="scanStatus == 'SUCCESS'" class="text-body-1"><v-icon title="Success" small style="color: #4caf50; margin-right:10px">fas fa-check</v-icon>Scan successfully completed.</div>
                        <div v-else-if="scanStatus == 'FAILED'" class="text-body-1"><v-icon title="Failed" small style="color: #EF5354; margin-right:10px">fas fa-times</v-icon>An error occurred while scanning the file.</div>
                        <div v-else-if="scanStatus == 'STOPPED'" class="text-body-1"><v-icon title="Stopped" small style="color: #EF5354; margin-right:10px">fas fa-ban</v-icon>Scan successfully stopped.</div>
                        <v-progress-linear :color="getProgressColor(scanStatus)" :indeterminate="scanStatus != 'FAILED' && (scanProgress == null || (scanProgress.value == 0 && scanStatus == 'IN PROGRESS'))" :value="scanProgress == null ? 0 : scanProgress.value" height="5" style="margin-top:10px"></v-progress-linear>
                        <v-card v-if="scanStatus == 'FAILED'" style="margin-top:15px">
                          <v-card-text>
                            <div class="text-body-1">{{ scanError }}</div>
                          </v-card-text>
                        </v-card>
                        <div v-if="scanProgress != null">
                          <div class="text-body-1" style="margin-top:10px">Progress: <span class="white--text" style="font-weight:500">{{ `${scanProgress.value} %` }}</span></div>
                          <div class="text-body-1" style="margin-top:10px">Data Transferred: <span class="white--text">{{ scanProgress.transferred }}</span></div>
                          <div class="text-body-1" style="margin-top:10px">Data Transfer Rate: <span class="white--text">{{ scanProgress.rate }}</span></div>
                          <div class="text-body-1" style="margin-top:10px">Elapsed Time: <span class="white--text">{{ scanProgress.elapsed }}</span></div>
                          <div v-if="scanProgress.eta != null" class="text-body-1" style="margin-top:10px">ETA: <span class="white--text">{{ scanProgress.eta }}</span></div>
                          <v-divider style="margin-top:10px"></v-divider>
                          <!-- SCAN SELECT -->
                          <div v-if="scanStatus == 'STOPPED' || scanError == null">
                            <div v-if="scanItems.length > 0" class="text-body-1" style="margin-top:15px">Choose the files to import:</div>
                            <v-toolbar dense flat color="#2e3131" style="margin-top:15px; border-top-left-radius:5px; border-top-right-radius:5px;">
                              <v-text-field v-model="scanSearch" append-icon="search" label="Search" color="white" single-line hide-details style="padding-right:10px"></v-text-field>
                            </v-toolbar>
                            <v-data-table v-model="scanSelected" :headers="scanHeaders" :items="scanItems" :search="scanSearch" :options="{ itemsPerPage: 5 }" :loading="loading" loading-text="Loading... Please wait" item-key="file" show-select class="elevation-1" mobile-breakpoint="0">
                              <template v-ripple v-slot:[`header.data-table-select`]="{}">
                                <v-simple-checkbox
                                  :value="scanItems.length == 0 ? false : scanSelected.length == scanItems.length"
                                  :indeterminate="scanSelected.length > 0 && scanSelected.length != scanItems.length"
                                  @click="scanSelected.length == scanItems.length ? scanSelected = [] : scanSelected = [...scanItems]">
                                </v-simple-checkbox>
                              </template>
                              <template v-slot:[`item.size`]="{ item }">
                                {{ formatBytes(item.size) }}
                              </template>
                            </v-data-table>
                            <div class="text-body-1" style="margin-top:15px">Selected Size: <span class="white--text" style="font-weight:500">{{ formatBytes(scanSelected.reduce((a, b) => a + b.size, 0)) }}</span></div>
                          </div>
                        </div>
                      </div>
                    </v-form>
                    <v-row no-gutters style="margin-top:20px;">
                      <v-col cols="auto" class="mr-auto">
                        <v-btn @click="nextStep" :disabled="(mode != 'cloud' && (source == null || source.length == 0)) || (scanID != null && scanSelected.length == 0) || (mode == 'cloud' && (awsObjectsSelected.length == 0 || awsObjectsSelected[0].name.endsWith('/')))" :loading="loading" color="primary">{{ mode == 'url' && size == null ? 'CHECK URL' : 'CONTINUE' }}</v-btn>
                        <v-btn @click="goBack" :disabled="loading" text style="margin-left:5px">CANCEL</v-btn>
                      </v-col>
                      <v-col cols="auto">
                        <v-btn v-if="scanID != null && scanProgress != null && scanStatus == 'IN PROGRESS'" color="primary" @click="stopScan(true)">STOP SCAN</v-btn>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-stepper-content>
              <v-stepper-step :complete="stepper > 2" step="2">DESTINATION</v-stepper-step>
              <v-stepper-content step="2" style="padding-top:0px; padding-left:10px">
                <v-card style="margin:5px">
                  <v-card-text>
                    <v-form ref="destinationForm" @submit.prevent>
                      <v-autocomplete @change="getDatabases" ref="server" :loading="loading" v-model="server" :items="serverItems" item-value="id" item-text="name" label="Server" auto-select-first :rules="[v => !!v || '']" style="padding-top:8px">
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                      <v-combobox ref="database" @keyup.enter="databaseKeyEnter" :disabled="!serverValidated" v-model="database" label="Database" :rules="[v => !!v || '']" :items="databaseItems" :search-input.sync="databaseSearch" style="padding-top:6px" hide-details>
                        <template v-slot:no-data>
                          <v-list-item>
                            <v-list-item-content>
                              <v-list-item-title>
                                No results matching "<strong>{{ databaseSearch }}</strong>". Press <kbd>Enter</kbd> to create a new database.
                              </v-list-item-title>
                            </v-list-item-content>
                          </v-list-item>
                        </template>
                      </v-combobox>
                      <v-checkbox v-if="databaseSearch != null && !databaseItems.includes(databaseSearch)" readonly v-model="createDatabase" label="Create database" hide-details style="margin-top:20px"></v-checkbox>
                      <v-checkbox v-else v-model="recreateDatabase" :disabled="server == null" label="Recreate database" hide-details style="margin-top:20px"></v-checkbox>
                    </v-form>
                    <v-row no-gutters style="margin-top:20px;">
                      <v-col cols="auto" class="mr-auto">
                        <v-btn :disabled="loading || server == null || database == null" color="primary" @click="nextStep">CONTINUE</v-btn>
                        <v-btn text @click="stepper = 1" style="margin-left:5px">CANCEL</v-btn>
                      </v-col>
                      <v-col cols="auto">
                        <v-btn @click="getServer(server)" :disabled="server == null" text>SERVER DETAILS</v-btn>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-stepper-content>
              <v-stepper-step step="3">OVERVIEW</v-stepper-step>
              <v-stepper-content step="3" style="margin:0px; padding:0px 10px 0px 0px">
                <div style="margin-left:10px">
                  <v-card style="margin:5px">
                    <v-toolbar dense flat color="#2e3131">
                      <v-toolbar-title class="subtitle-1">SOURCE</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                      <div class="subtitle-1 white--text">METHOD</div>
                      <v-radio-group v-model="mode" readonly style="margin-top:10px; margin-bottom:15px" hide-details>
                        <v-radio value="file">
                          <template v-slot:label>
                            <v-icon small color="#23cba7" style="margin-left:7px; margin-right:15px">fas fa-file</v-icon>
                            File
                          </template>
                        </v-radio>
                        <v-radio value="url">
                          <template v-slot:label>
                            <v-icon small color="#ff9800" style="margin-left:6px; margin-right:12px">fas fa-link</v-icon>
                            URL
                          </template>
                        </v-radio>
                        <v-radio value="cloud">
                          <template v-slot:label>
                            <v-icon color="#19b5fe" style="font-size:18px; margin-left:3px; margin-right:8px">fas fa-cloud</v-icon>
                            Cloud
                          </template>
                        </v-radio>
                      </v-radio-group>
                      <div v-if="['file','url'].includes(mode)">
                        <v-text-field readonly v-model="source" :label="mode == 'file' ? 'File' : 'URL'" style="margin-top:15px" hide-details></v-text-field>
                        <v-select v-if="mode == 'url'" readonly v-model="format" :items="['.sql','.gz','.tar','.tar.gz']" label="Format" required :rules="[v => !!v || '']" hide-details style="margin-top:15px"></v-select>
                        <div class="text-body-1" style="margin-top:20px">File Size: <span class="white--text" style="font-weight:500">{{ formatBytes(size) }}</span></div>
                      </div>
                      <div v-else-if="mode == 'cloud'">
                        <div class="subtitle-1 white--text" style="margin-bottom:15px">CLOUD KEY</div>
                        <v-data-table :headers="cloudKeysHeaders" :items="cloudKeysSelected" item-key="id" hide-default-footer class="elevation-1" mobile-breakpoint="0">
                          <template v-slot:item="{ item }">
                            <tr>
                              <td v-for="header in cloudKeysHeaders" :key="header.value">
                                <div v-if="header.value == 'type'">
                                  <v-icon v-if="item.type == 'aws'" size="22" color="#e47911" title="Amazon Web Services">fab fa-aws</v-icon>
                                  <v-icon v-else-if="item.type == 'google'" size="20" color="#4285F4" title="Google Cloud" style="margin-left:4px">fab fa-google</v-icon>
                                </div>
                                <div v-else-if="header.value == 'shared'">
                                  <v-icon v-if="!item.shared" small title="Personal" color="warning" style="margin-right:6px; margin-bottom:2px">fas fa-user</v-icon>
                                  <v-icon v-else small title="Shared" color="#EB5F5D" style="margin-right:6px; margin-bottom:2px">fas fa-users</v-icon>
                                  {{ !item.shared ? 'Personal' : 'Shared' }}
                                </div>
                                <div v-else>
                                  {{ item[header.value] }}
                                </div>
                              </td>
                            </tr>
                          </template>
                        </v-data-table>
                        <div class="subtitle-1 white--text" style="margin-top:15px; margin-bottom:15px">OBJECT</div>
                        <v-data-table :headers="awsObjectsHeaders" :items="awsObjectsSelected" item-key="name" hide-default-footer class="elevation-1" mobile-breakpoint="0">
                          <template v-slot:item="{ item }">
                            <tr>
                              <td v-for="header in awsObjectsHeaders" :key="header.value">
                                <span v-if="header.value == 'name'">
                                  <v-icon size="16" :color="item['name'].endsWith('/') ? '#e47911' : '#23cba7'" style="margin-right:10px; margin-bottom:2px">{{ item['name'].endsWith('/') ? 'fas fa-folder' : 'far fa-file'}}</v-icon>
                                  {{ item.name }}
                                </span>
                                <span v-else-if="header.value == 'type'">
                                  {{ item['name'].endsWith('/') ? 'Folder' : item['name'].indexOf('.') == '-1' ? '-' : item['name'].substring(item['name'].lastIndexOf(".") + 1) }}
                                </span>
                                <span v-else-if="header.value == 'size'">
                                  {{ formatBytes(item.size) }}
                                </span>
                                <span v-else>{{ item[header.value] }}</span>
                              </td>
                            </tr>
                          </template>
                        </v-data-table>
                      </div>
                      <div v-if="scanItems.length > 0">
                        <div class="subtitle-1 white--text" style="margin-top:15px; margin-bottom:15px">FILES</div>
                        <v-data-table readonly :headers="scanHeaders" :items="scanSelected" :search="scanSearch" :hide-default-footer="scanItems.length < 11" item-key="file" class="elevation-1" mobile-breakpoint="0">
                          <template v-slot:[`item.size`]="{ item }">
                            {{ formatBytes(item.size) }}
                          </template>
                        </v-data-table>
                        <div class="text-body-1" style="margin-top:20px">Selected Size: <span class="white--text" style="font-weight:500">{{ formatBytes(scanSelected.reduce((a, b) => a + b.size, 0)) }}</span></div>
                      </div>
                    </v-card-text>
                  </v-card>
                  <v-card style="margin:10px 5px 5px 5px">
                    <v-toolbar dense flat color="#2e3131">
                      <v-toolbar-title class="subtitle-1">DESTINATION</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                      <v-autocomplete readonly v-model="server" :items="serverItems" item-value="id" item-text="name" label="Server" :rules="[v => !!v || '']" style="padding-top:8px">
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                      <v-text-field readonly v-model="database" label="Database" :rules="[v => !!v || '']" style="padding-top:6px" hide-details></v-text-field>
                      <v-checkbox v-if="databaseSearch != null && !databaseItems.includes(databaseSearch)" readonly v-model="createDatabase" label="Create database" hide-details style="margin-top:20px"></v-checkbox>
                      <v-checkbox v-else v-model="recreateDatabase" readonly label="Recreate database" hide-details style="margin-top:20px"></v-checkbox>
                    </v-card-text>
                  </v-card>
                </div>
                <div style="margin-left:15px; margin-top:20px; margin-bottom:5px">
                  <v-btn :disabled="loading" :loading="loading" @click="submitImport" color="#00b16a">IMPORT</v-btn>
                  <v-btn :disabled="loading" @click="stepper = 2" color="#EF5354" style="margin-left:5px">CANCEL</v-btn>
                </div>
              </v-stepper-content>
            </v-stepper>
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>
    <!----------------->
    <!-- FILE DIALOG -->
    <!----------------->
    <v-dialog v-model="dialog" persistent max-width="640px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-spinner</v-icon>UPLOADING</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding:0px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12 style="padding:15px">
                <div class="text-body-1">{{ progress != 100 ? 'Uploading file. Please wait...' : 'File successfully uploaded.' }}</div>
                <v-progress-linear :color="progress != 100 ? '#ff9800' : '#00b16a'" height="5" :value="progress" style="margin-top:10px"></v-progress-linear>
                <v-card style="margin-top:10px">
                  <v-card-text>
                    <div class="text-body-1">
                      <div><span class="white--text">Progress: <span style="color:#fa8131; font-weight:500">{{ `${progress} % `}}</span></span>{{ progressText }}</div>
                    </div>
                  </v-card-text>
                </v-card>
                <v-divider style="margin-top:15px"></v-divider>
                <div style="margin-top:15px">
                  <v-btn :disabled="progress == 100" @click="cancelImport" color="#EF5354">CANCEL</v-btn>
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
import axios from 'axios';
import pretty from 'pretty-bytes';
import EventBus from '../event-bus'

export default {
  data() {
    return {
      loading: false,
      stepper: 1,
      // Source
      mode: 'file',
      source: null,
      format: null,
      size: null,
      fileObject: null,
      // Scan
      scanID: null,
      scanStatus: '',
      scanProgress: null,
      scanItems: [],
      scanHeaders: [
        { text: 'File', value: 'file',  width: '50%' },
        { text: 'Size', value: 'size' },
      ],
      scanSearch: '',
      scanSelected: [],
      scanError: null,
      scanTimer: null,
      // Cloud Keys
      cloudKeysHeaders: [
        { text: 'Name', align: 'left', value: 'name' },
        { text: 'Type', align: 'left', value: 'type' },
        { text: 'Access Key', align: 'left', value: 'access_key'},
        { text: 'Scope', align: 'left', value: 'shared' },
      ],
      cloudKeysItems: [],
      cloudKeysSelected: [],
      cloudKeysSearch: '',
      cloudPath: ['Cloud Keys'],
      // AWS Buckets
      awsBucketsSelected: [],
      awsBucketsHeaders: [
        { text: 'Name', align: 'left', value: 'name' },
        { text: 'Region', align: 'left', value: 'region' },
      ],
      awsBucketsItems: [],
      awsBucketsSearch: '',
      // AWS Objects
      awsObjectsSelected: [],
      awsObjectsHeaders: [
        { text: 'Name', align: 'left', value: 'name' },
        { text: 'Type', align: 'left', value: 'type' },
        { text: 'Last Modified', align: 'left', value: 'last_modified' },
        { text: 'Size', align: 'left', value: 'size' },
        { text: 'Storage Class', align: 'left', value: 'storage_class' },
      ],
      awsObjectsItems: [],
      awsObjectsSearch: '',
      // Destination
      serverItems: [],
      server: null,
      serverValidated: false,
      databaseItems: [],
      database: null,
      databaseSearch: null,
      createDatabase: true,
      recreateDatabase: false,
      // Dialog
      dialog: false,
      progress: 0,
      progressText: '',
      cancelToken: null,
      // Previous Route
      prevRoute: null
    }
  },
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    readOnly: function() { return !this.owner && (Object.keys(this.serverItem).length == 0 || this.serverItem.shared == 1) },
  },
  beforeRouteEnter(to, from, next) {
    next(vm => {
      vm.prevRoute = from
    })
  },
  beforeRouteLeave(to, from, next) {
    this.stopScan(false)
    next()
  },
  created() {
    this.getServers()
  },
  watch: {
    mode(val) {
      this.clearScan()
      if (val == 'cloud') this.getCloud()
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
      })
    },
    stepper(val) {
      if (val == 2) {
        requestAnimationFrame(() => {
          if (typeof this.$refs.server !== 'undefined') this.$refs.server.focus()
        })
      }
      if (val == 3) {
        requestAnimationFrame(() => {
          if (typeof this.$refs.server !== 'undefined') this.$refs.server.blur()
          if (typeof this.$refs.database !== 'undefined') this.$refs.database.blur()
        })
      }
    },
    fileObject(val) {
      if (val == null) {
        this.source = null
        this.size = null
      }
      else {
        this.source = val.name
        this.size = val.size
      }
    },
    source() {
      if (this.mode == 'url') this.clearScan()
    },
  },
  methods: {
    clearScan() {
      this.size = null
      this.scanID = null
      this.scanSearch = ''
      this.scanItems = []
      this.scanSelected = []
      this.scanProgress = null
      this.scanError = null
    },
    cloudPathClick (item, index) {
      if (index == this.cloudPath.length - 1) return
      this.clearScan()
      // Cloud Keys
      if (index == 0) {
        this.cloudPath = ['Cloud Keys']
        this.cloudKeysSelected = []
        this.awsBucketsSelected = []
        this.awsBucketsItems = []
        this.awsObjectsSelected = []
        this.awsObjectsItems = []
        this.getCloud()
      }
      // Amazon S3 Buckets
      else if (index == 1) {
        this.awsBucketsSelected = []
        this.awsObjectsSelected = []
        this.cloudPath = ['Cloud Keys', this.cloudPath[1]]
        this.getAWSBuckets()
      }
      // Amazon S3 Folder
      else {
        this.cloudPath = this.cloudPath.slice(0, this.cloudPath.indexOf(item)+1)
        this.awsObjectsSelected = []
        this.getAWSObjects(false)
      }
    },
    cloudKeysClick(item) {
      this.cloudKeysSelected = [item]
      this.getAWSBuckets()
    },
    awsBucketsClick(item) {
      this.awsObjectsSelected = []
      this.awsBucketsSelected = [item]
      this.getAWSObjects(false)
    },
    awsObjectsClick(item) {
      if (this.loading || (this.scanID != null && !(['SUCCESS','FAILED','STOPPED'].includes(this.scanStatus)))) return
      this.clearScan()
      this.awsObjectsSelected = [item]
      if (item.name.endsWith('/')) this.getAWSObjects(false)
    },
    getServers() {
      this.loading = true
      axios.get('/utils/servers')
        .then((response) => {
          this.serverItems = response.data.servers
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getDatabases() {
      if (this.server == null) this.databaseItems = []
      else {
        this.loading = true
        const payload = { server_id: this.server }
        axios.get('/utils/databases', { params: payload })
          .then((response) => {
            this.serverValidated = true
            this.databaseItems = response.data.databases.map(x => x.name)
            this.$nextTick(() => {
              this.$refs.destinationForm.resetValidation()
              this.$refs.server.blur()
              this.$refs.database.focus()
            })
          })
          .catch((error) => {
            this.serverValidated = false
            this.databaseItems = []
            this.database = null
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
          .finally(() => this.loading = false)
      }
    },
    getCloud() {
      this.loading = true
      axios.get('/inventory/cloud')
        .then((response) => {
          this.cloudKeysItems = response.data.data
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getAWSBuckets() {
      // Test Connection
      this.loading = true
      const payload = { key: this.cloudKeysSelected[0]['id'] }
      axios.get('/utils/imports/s3/buckets', { params: payload })
        .then((response) => {
          this.parseAWSBuckets(response.data.buckets)
          this.cloudKeysSearch = ''
        })
        .catch((error) => {
          this.cloudKeysSelected = []
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    parseAWSBuckets(buckets) {
      this.awsBucketsItems = buckets
      this.cloudPath = ['Cloud Keys', this.cloudKeysSelected[0].type == 'aws' ? 'Amazon S3' : 'Google Cloud']
    },
    getAWSObjects(search, event) {
      if (event !== undefined && event.key.length > 1 && !(['Backspace','Delete','Meta','Control','Enter'].includes(event.key))) return
      if (event === undefined) this.loading = true
      this.awsObjectsItems = []
      const payload = { 
        key: this.cloudKeysSelected[0]['id'],
        bucket: this.cloudPath.length > 3 ? this.cloudPath[2] : this.awsBucketsSelected[0]['name'],
        prefix: this.parseAWSPrefix(search),
        path: this.parseAWSPath(),
      }
      axios.get('/utils/imports/s3/objects', { params: payload })
        .then((response) => {
          this.parseAWSObjects(response.data.objects, search)
          this.awsBucketsSearch = ''
          if (event === undefined) this.awsObjectsSearch = ''
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    parseAWSPath() {
      let path = this.cloudPath.slice(3).join('')
      if (this.awsObjectsSelected.length > 0 && this.awsObjectsSelected[0].name.endsWith('/')) {
        path += this.awsObjectsSelected[0].name
      }
      return path
    },
    parseAWSPrefix(search) {
      let path = this.cloudPath.slice(3).join('')
      if (search) return path += this.awsObjectsSearch
      if (this.awsObjectsSelected.length > 0 && this.awsObjectsSelected[0].name.endsWith('/')) path += this.awsObjectsSelected[0].name
      return path
    },
    parseAWSObjects(objects, search) {
      this.awsObjectsHeaders = [
        { text: 'Name', align: 'left', value: 'name' },
        { text: 'Type', align: 'left', value: 'type' },
        { text: 'Last Modified', align: 'left', value: 'last_modified' },
        { text: 'Size', align: 'left', value: 'size' },
        { text: 'Storage Class', align: 'left', value: 'storage_class' },
      ]
      this.awsObjectsItems = objects
      if (!search) {
        if (this.cloudPath.length == 2) this.cloudPath.push(this.awsBucketsSelected[0]['name'])
        else if (this.awsObjectsSelected.length != 0) this.cloudPath.push(this.awsObjectsSelected[0]['name'])
      }
      this.awsObjectsSelected = []
    },
    goBack() {
      if (this.stepper == 1 && this.scanID != null) this.stopScan(false)
      if (this.prevRoute.path == '/admin/utils/imports') this.$router.push('/admin/utils/imports')
      else this.$router.push('/utils/imports')
    },
    nextStep() {
      if (this.stepper == 1 && !this.$refs.sourceForm.validate()) return
      else if (this.stepper == 2 && !this.$refs.destinationForm.validate()) return
      if (this.stepper == 1 && ['url','cloud'].includes(this.mode) && this.scanID == null) {
        if (this.mode == 'url' && this.size != null) this.stepper = this.stepper + 1
        else this.scanFile()
      }
      else {
        // Stop Scan (if there's an existing one) & Check Selected Files
        if (this.stepper == 1) {
          this.stopScan()
          if (this.scanSelected.length > 0) {
            let extensions = this.scanSelected.map(x => x.file.lastIndexOf('.') === -1 ? '' : x.file.substring(x.file.lastIndexOf('.') + 1, x.file.length))
            if (!(extensions.every(x => x === extensions[0]))) {
              EventBus.$emit('send-notification', 'Selected file extensions must be the same', '#EF5354')
              return
            }
            if (extensions.some(x => !(['sql','gz'].includes(x)))) {
              EventBus.$emit('send-notification', 'Selected file extensions must be .sql or .gz', '#EF5354')
              return
            }
          }
        }
        this.stepper = this.stepper + 1
      }
    },
    submitImport() {
      if (this.mode == 'file') this.checkFileImport()
      else if (this.mode == 'url') this.submitURLImport()
      else if (this.mode == 'cloud') this.submitCloudImport()
    },
    checkFileImport() {
      this.loading = true
      axios.get('/utils/imports/check', { params: { size: this.size }})
        .then((response) => {
          if (response.data.check) this.submitFileImport()
          else EventBus.$emit('send-notification', 'There is not enough space left to proceed with the import.', '#EF5354')
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    submitFileImport() {
      this.progress = 0
      this.progressText = ''
      this.dialog = true
      // Build import
      const data = new FormData();
      data.append('mode', this.mode)
      data.append('source', this.fileObject)
      data.append('size', this.fileObject.size)
      data.append('server', this.server)
      data.append('database', this.database)
      data.append('createDatabase', !this.databaseItems.includes(this.databaseSearch))
      data.append('recreateDatabase', this.databaseItems.includes(this.databaseSearch) ? this.recreateDatabase : false)
      data.append('dropDatabase', this.dropDatabase)
      data.append('url', window.location.protocol + '//' + window.location.host)
      // Build request options
      const CancelToken = axios.CancelToken;
      this.cancelToken = CancelToken.source();
      const options = {
        onUploadProgress: (progressEvent) => {
          var percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          this.progress = percentCompleted
          this.progressText = '(' + this.formatBytes(progressEvent.loaded) + ' / ' + this.formatBytes(progressEvent.total) + ')'
        },
        cancelToken: this.cancelToken.token
      }
      // Start import
      this.start = true
      axios.post('/utils/imports', data, options)
      .then((response) => {
        if (this.progress == 100) {
          EventBus.$emit('send-notification', "File successfully uploaded.", "#00b16a")
          // Refresh user coins
          this.$store.dispatch('app/coins', response.data.coins)
          setTimeout(() => this.$router.push('/utils/imports/' + response.data.uri), 1000)
        }
      })
      .catch((error) => {
        this.dialog = false
        if (axios.isCancel(error)) EventBus.$emit('send-notification', "The upload process has been stopped.", "info")
        else if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
    },
    scanFile() {
      this.loading = true
      this.clearScan()
      let payload = { mode: this.mode }
      if (this.mode == 'url') payload['source'] = this.source
      else if (this.mode == 'cloud') {
        payload = {
          ...payload,
          source: this.awsObjectsSelected[0]['key'],
          cloud_id: this.cloudKeysSelected[0]['id'],
          bucket: this.cloudPath[2],
          region: this.awsBucketsSelected[0]['region']
        }
      }
      axios.post('/utils/imports/scan', payload)
      .then((response) => {
        this.size = response.data.size
        if ('id' in response.data) {
          this.scanID = response.data.id
          this.getScan()
        }
        else if (this.mode == 'cloud') {
          this.stepper = this.stepper + 1
        }
      })
      .catch((error) => {
        this.loading = false
        if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
      .finally(() => this.loading = false)
    },
    getScan() {
      axios.get('/utils/imports/scan', { params: { id: this.scanID }})
      .then((response) => {
        this.scanStatus = response.data.status
        this.scanProgress = this.parseProgress(response.data.progress)
        this.scanItems = response.data.data == null ? [] : response.data.data
        this.scanError = response.data.error
        if ((this.scanProgress == null && this.scanStatus != 'FAILED') || this.scanStatus == 'IN PROGRESS') {
          clearTimeout(this.scanTimer)
          if (this.$router.currentRoute.name == 'utils.imports.new') this.scanTimer = setTimeout(this.getScan, 1000)
        }
      })
      .catch((error) => {
        if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
    },
    stopScan(notification) {
      if (this.scanStatus != 'IN PROGRESS') return
      const payload = { id: this.scanID }
      axios.post('/utils/imports/scan/stop', payload)
      .then((response) => {
        if (notification) EventBus.$emit('send-notification', response.data.message, '#00b16a')
      })
      .catch((error) => {
        if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
    },
    parseProgress(progress) {
      if (progress == null || typeof progress !== 'object') return null
      progress.value = parseInt(progress.value.slice(0, -1))
      progress.transferred = this.parseMetric(progress.transferred)
      progress.rate = this.parseMetric(progress.rate)
      return progress
    },
    parseMetric(val) {
      for (let i = val.length; i >= 0; --i) {
        if (Number.isInteger(parseInt(val[i]))) {
          return val.substring(0, i+1) + ' ' + val.substring(i+1, val.length)
        }
      }
      return val
    },
    submitURLImport() {
      this.loading = true
      const payload = {
        mode: this.mode,
        source: this.source,
        format: this.format,
        selected: this.scanSelected,
        server: this.server,
        database: this.database,
        createDatabase: !this.databaseItems.includes(this.databaseSearch),
        recreateDatabase: this.databaseItems.includes(this.databaseSearch) ? this.recreateDatabase : false,
        dropDatabase: this.dropDatabase,
        url: window.location.protocol + '//' + window.location.host
      }
      axios.post('/utils/imports', payload)
      .then((response) => {
        // Refresh user coins
        this.$store.dispatch('app/coins', response.data.coins)
        this.$router.push('/utils/imports/' + response.data.uri)
      })
      .catch((error) => {
        if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
      .finally(() => this.loading = false)
    },
    submitCloudImport() {
      this.loading = true
      const payload = {
        mode: this.mode,
        source: this.awsObjectsSelected[0]['key'],
        cloud: this.cloudKeysSelected[0],
        bucket: this.cloudPath[2],
        region: this.awsBucketsSelected[0]['region'],
        object: this.awsObjectsSelected[0],
        selected: this.scanSelected,
        server: this.server,
        database: this.database,
        createDatabase: !this.databaseItems.includes(this.databaseSearch),
        recreateDatabase: this.databaseItems.includes(this.databaseSearch) ? this.recreateDatabase : false,
        dropDatabase: this.dropDatabase,
        url: window.location.protocol + '//' + window.location.host
      }
      axios.post('/utils/imports', payload)
      .then((response) => {
        // Refresh user coins
        this.$store.dispatch('app/coins', response.data.coins)
        this.$router.push('/utils/imports/' + response.data.uri)
      })
      .catch((error) => {
        if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
      .finally(() => this.loading = false)
    },
    cancelImport() {
      this.cancelToken.cancel()
      this.dialog = false
    },
    getServer(server_id) {
      EventBus.$emit('get-server', server_id)
    },
    getProgressColor(status) {
      if (status == 'IN PROGRESS') return '#ff9800'
      if (status == 'SUCCESS') return '#4caf50'
      if (['FAILED','STOPPED'].includes(status)) return '#EF5354'
    },
    formatBytes(size) {
      if (size == null) return null
      return pretty(size, {binary: true}).replace('i','')
    },
    capitalize(text) {
      let wordsArray = text.toLowerCase().split(' ')
      let capsArray = wordsArray.map(word => word[0].toUpperCase() + word.slice(1))
      return capsArray.join(' ')
    },
    validURL(str) {
      var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
      return !!pattern.test(str);
    },
    databaseKeyEnter() {
      this.$refs.database.blur()
    },
  }
}
</script>