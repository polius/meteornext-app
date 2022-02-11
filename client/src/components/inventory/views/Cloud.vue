<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">CLOUD KEYS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn text @click="newCloud()"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1 || selected[0].secured == 1" text @click="editCloud()"><v-icon small style="margin-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn :disabled="selected.length != 1 || selected[0].secured == 1" @click="cloneCloud()" text><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn :disabled="selected.length == 0 || selected.some(x => x.secured) || (!owner && selected.some(x => x.shared))" text @click="deleteCloud()"><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="testCloud" :disabled="selected.length != 1" title="Test an auxiliary connection" text><v-icon small style="margin-right:10px">fas fa-server</v-icon>TEST</v-btn>
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
          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
          {{ item.name }}
        </template>
        <template v-slot:[`item.type`]="{ item }">
          <v-icon v-if="item.type == 'aws'" size="22" color="#e47911" title="Amazon Web Services">fab fa-aws</v-icon>
          <v-icon v-else-if="item.type == 'google'" size="20" color="#4285F4" title="Google Cloud" style="margin-left:4px">fab fa-google</v-icon>
        </template>
      </v-data-table>
    </v-card>
    <!------------>
    <!-- DIALOG -->
    <!------------>
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
                <v-alert v-if="!owner && item.shared" color="warning" outlined dense style="margin-bottom:30px"><v-icon color="warning" style="font-size:16px; margin-bottom:3px; margin-right:10px">fas fa-exclamation-triangle</v-icon>This resource cannot be edited. You are not a group owner.</v-alert>
                <v-form v-if="mode != 'delete'" ref="form" style="margin-top:15px; margin-bottom:15px">
                  <v-text-field ref="field" v-model="item.name" :readonly="readonly" :rules="[v => !!v || '']" label="Name" required style="margin-top:0px; padding-top:0px"></v-text-field>
                  <v-select v-model="item.type" :items="[{id: 'aws', name: 'Amazon Web Services'}]" item-value="id" :readonly="readonly" :rules="[v => !!v || '']" label="Type" required style="padding-top:0px">
                    <template v-slot:[`selection`]="{ item }">
                      <v-icon v-if="item.id == 'aws'" size="22" color="#e47911" style="margin-right:8px">fab fa-aws</v-icon>
                      <v-icon v-else-if="item.id == 'google'" size="20" color="#4285F4" style="margin-right:8px">fab fa-google</v-icon>
                      {{ item.id == 'aws' ? 'Amazon Web Services' : 'Google Cloud' }}
                    </template>
                    <template v-slot:[`item`]="{ item }">
                      <v-icon v-if="item.id == 'aws'" size="22" color="#e47911" style="margin-right:8px">fab fa-aws</v-icon>
                      <v-icon v-else-if="item.id == 'google'" size="20" color="#4285F4" style="margin-left:4px; margin-right:12px">fab fa-google</v-icon>
                      {{ item.id == 'aws' ? 'Amazon Web Services' : 'Google Cloud' }}
                    </template>
                  </v-select>
                  <div>
                    <v-text-field v-model="item.access_key" :readonly="readonly" :rules="[v => !!v || '']" label="Access Key" autocomplete="username" style="padding-top:0px" hide-details></v-text-field>
                    <v-text-field v-if="item.secret_key == null || (typeof item.secret_key !== 'object')" v-model="item.secret_key" :readonly="readonly" :rules="[v => !!v || '']" label="Secret Key" :append-icon="showSecret ? 'mdi-eye' : 'mdi-eye-off'" :type="showSecret ? 'text' : 'password'" @click:append="showSecret = !showSecret" autocomplete="new-password" style="margin-top:15px; margin-bottom:20px" hide-details></v-text-field>
                    <v-card v-else style="height:52px; margin-top:15px">
                      <v-row no-gutters>
                        <v-col cols="auto" style="display:flex; margin:15px">
                          <v-icon color="#00b16a" style="font-size:20px">fas fa-key</v-icon>
                        </v-col>
                        <v-col>
                          <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a Secret Key</div>
                        </v-col>
                        <v-col cols="auto" class="text-right">
                          <v-btn v-if="!readonly" @click="item.secret_key = null" icon title="Remove Secret Key" style="margin:8px"><v-icon style="font-size:18px">fas fa-times</v-icon></v-btn>
                        </v-col>
                      </v-row>
                    </v-card>
                    <v-card style="margin-top:15px; margin-bottom:20px;">
                      <v-toolbar flat dense color="#2e3131">
                        <v-toolbar-title class="white--text subtitle-1">BUCKETS</v-toolbar-title>
                        <v-divider class="mx-3" inset vertical></v-divider>
                        <v-toolbar-items style="padding-left:0px;">
                          <v-btn text @click='newBucket()'><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                          <v-btn :disabled="bucketsSelected.length != 1" text @click="editBucket()"><v-icon small style="margin-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                          <v-btn :disabled="bucketsSelected.length == 0" text @click='deleteBucket()'><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                        </v-toolbar-items>
                        <v-divider class="mx-3" inset vertical></v-divider>
                        <v-text-field v-model="bucketsSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                      </v-toolbar>
                      <v-divider></v-divider>
                      <v-data-table v-model="bucketsSelected" :headers="bucketsHeaders" :items="bucketsItems" :search="bucketsSearch" :hide-default-header="bucketsItems.length == 0" :hide-default-footer="bucketsItems.length < 6" :options="{itemsPerPage: 5}" item-key="name" show-select class="elevation-1" style="padding-top:5px;" mobile-breakpoint="0">
                        <template v-ripple v-slot:[`header.data-table-select`]="{}">
                          <v-simple-checkbox
                            :value="bucketsItems.length == 0 ? false : bucketsSelected.length == bucketsItems.length"
                            :indeterminate="bucketsSelected.length > 0 && bucketsSelected.length != bucketsItems.length"
                            @click="bucketsSelected.length == bucketsItems.length ? bucketsSelected = [] : bucketsSelected = [...bucketsItems]">
                          </v-simple-checkbox>
                        </template>
                      </v-data-table>
                    </v-card>
                  </div>
                </v-form>
                <div v-else class="subtitle-1" style="margin-bottom:12px">Are you sure you want to delete the selected cloud keys?</div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :loading="loading" color="#00b16a" @click="submitCloud()">CONFIRM</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="testConnection()">Test Cloud Key</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- BUCKETS DIALOG -->
    <!-------------------->
    <v-dialog v-model="bucketsDialog" max-width="600px">
      <v-toolbar flat dense color="primary">
        <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:1px">{{bucketsDialogMode == 'new' ? 'fas fa-plus' : bucketsDialogMode == 'edit' ? 'fas fa-feather-alt' : 'fas fa-minus'}}</v-icon>{{ `${bucketsDialogMode.toUpperCase()} BUCKET` }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="bucketsDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="bucketsForm" @submit.prevent>
                  <div v-if="bucketsDialogMode == 'delete'" class="subtitle-1" style="margin-top:3px">Are you sure you want to remove the selected buckets from the list?</div>
                  <v-text-field v-else ref="bucketsName" v-model="bucketsDialogName" v-on:keyup.enter="bucketsDialogConfirm()" :rules="[v => !!v || '']" label="Name" hide-details style="padding-top:8px"></v-text-field>
                </v-form>
                <v-divider style="margin-top:15px; margin-bottom:15px"></v-divider>
                <v-btn color="#00b16a" @click="bucketsDialogConfirm()">Confirm</v-btn>
                <v-btn color="#EF5354" @click="bucketsDialog = false" style="margin-left:5px">Cancel</v-btn>
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
                  <v-checkbox v-model="columnsRaw" label="Type" value="type" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Access Key" value="access_key" hide-details style="margin-top:5px"></v-checkbox>
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
    loading: true,
    filter: 'all',
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Type', align: 'left', value: 'type' },
      { text: 'Access Key', align: 'left', value: 'access_key'},
    ],
    cloud: [],
    items: [],
    selected: [],
    search: '',
    item: { name: '', type: '', access_key: '', secret_key: '', buckets: [], shared: false },
    mode: '',
    showSecret: false,
    // Dialog
    dialog: false,
    dialog_title: '',
    bucketsHeaders: [
      { text: 'Name', align: 'left', value: 'name' },
    ],
    bucketsItems: [],
    bucketsSelected: [],
    bucketsSearch: '',
    // Buckets Dialog
    bucketsDialog: false,
    bucketsDialogMode: '',
    bucketsDialogName: '',
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','type','access_key','shared'],
    columnsRaw: [],
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    readonly: function() { return this.item.shared == 1 && !this.owner },
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  created() {
    this.getCloud()
  },
  methods: {
    getCloud() {
      this.loading = true
      axios.get('/inventory/cloud')
        .then((response) => {
          this.cloud = response.data.data
          this.items = response.data.data
          this.filterBy(this.filter)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    newCloud() {
      this.mode = 'new'
      this.item = { name: '', type: '', access_key: '', secret_key: '', buckets: [], shared: false }
      this.bucketsItems = []
      this.bucketsSelected = []
      this.dialog_title = 'NEW CLOUD KEY'
      this.dialog = true
    },
    cloneCloud() {
      this.mode = 'clone'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item.shared = (!this.owner) ? false : this.item.shared
      this.bucketsItems = this.selected[0]['buckets'].map(x => ({name: x}))
      this.bucketsSelected = []
      this.dialog_title = 'CLONE CLOUD KEY'
      this.dialog = true
    },
    editCloud() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      if ('buckets' in this.selected[0]) this.bucketsItems = this.selected[0]['buckets'].map(x => ({name: x}))
      this.bucketsSelected = []
      this.dialog_title = 'EDIT CLOUD KEY'
      this.dialog = true
    },
    deleteCloud() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE CLOUD'
      this.dialog = true
    },
    testCloud() {
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.testConnection()
    },
    submitCloud() {
      if (['new','clone'].includes(this.mode)) this.newCloudSubmit()
      else if (this.mode == 'edit') this.editCloudSubmit()
      else if (this.mode == 'delete') this.deleteCloudSubmit()
    },
    async newCloudSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Add item in the DB
      this.loading = true
      const payload = {...this.item, buckets: this.bucketsItems.map(x => x.name)}
      axios.post('/inventory/cloud', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getCloud()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    async editCloudSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Edit item in the DB
      this.loading = true
      const payload = {...this.item, buckets: this.bucketsItems.map(x => x.name)}
      axios.put('/inventory/cloud', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getCloud()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteCloudSubmit() {
      this.loading = true
      // Build payload
      const payload = { cloud: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/inventory/cloud', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getCloud()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    testConnection() {
      // Test Connection
      this.loading = true
      let payload = {}
      if ('secret_key' in this.item && this.item.secret_key != null && typeof this.item.secret_key !== 'object') {
        payload = { access_key: this.item['access_key'], secret_key: this.item['secret_key'] }
      }
      else payload = { id: this.selected[0]['id'] }
      axios.post('/inventory/cloud/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    filterBy(val) {
      this.filter = val
      if (val == 'all') this.items = this.cloud.slice(0)
      else if (val == 'personal') this.items = this.cloud.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.cloud.filter(x => x.shared)
    },
    newBucket() {
      this.bucketsDialogMode = 'new'
      this.bucketsDialogName = ''
      this.bucketsDialog = true
    },
    editBucket() {
      this.bucketsDialogMode = 'edit'
      this.bucketsDialogName = this.bucketsSelected[0]['name']
      this.bucketsDialog = true
    },
    deleteBucket() {
      this.bucketsDialogMode = 'delete'
      this.bucketsDialog = true
    },
    bucketsDialogConfirm() {
      // Check constraints
      if (['new','edit'].includes(this.bucketsDialogMode)) {
        if (!this.$refs.bucketsForm.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
          return
        }
        if (this.bucketsItems.some(x => x.name == this.bucketsDialogName.trim()) && (this.bucketsDialogMode == 'new' || this.bucketsSelected[0]['name'] != this.bucketsDialogName.trim())) {
          this.notification('This bucket name already exists','#EF5354')
          return
        }
      }
      if (this.bucketsDialogMode == 'new') this.bucketsItems.push({name: this.bucketsDialogName})
      else if (this.bucketsDialogMode == 'edit') {
        this.bucketsItems = this.bucketsItems.filter(x => x.name != this.bucketsSelected[0]['name'])
        this.bucketsItems.push({name: this.bucketsDialogName})
      }
      else if (this.bucketsDialogMode == 'delete') this.bucketsItems = this.bucketsItems.filter(x => !this.bucketsSelected.some(y => y.name == x.name))
      this.bucketsItems.sort((a, b) => a.name.localeCompare(b.name))
      this.bucketsSelected = []
      this.bucketsDialog = false
    },
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','type','access_key','shared']
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
      this.showSecret = false
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.field !== 'undefined' && !this.readonly) this.$refs.field.focus()
      })
    },
    bucketsDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.bucketsForm !== 'undefined') this.$refs.bucketsForm.resetValidation()
        if (typeof this.$refs.bucketsName !== 'undefined') this.$refs.bucketsName.focus()
      })
    }
  }
}
</script>