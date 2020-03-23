<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">{{ toolbar_title }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon title="Go back" @click="goBack()" style="margin-right:-5px;"><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn>
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
            <v-text-field v-model="group.coins_day" label="Coins per day" :rules="[v => v == parseInt(v) && v >= 0 || '']" required></v-text-field>
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
                <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>JOBS</span></v-tab>    
              </v-tabs>
            </div>

            <!-- INVENTORY -->
            <v-card v-if="tabs==0" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">INVENTORY</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch label="Access Inventory" color="info" style="margin-top:0px;"></v-switch>
              </v-card-text>
            </v-card>

            <!-- DEPLOYMENTS -->
            <v-card v-if="tabs==1" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">DEPLOYMENTS</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch v-model="group.deployments_enable" label="Perform Deployments" color="info" style="margin-top:0px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enable" v-model="group.deployments_basic" label="BASIC" color="#eb974e" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enable" v-model="group.deployments_pro" label="PRO" color="rgb(235, 95, 93)" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
                <v-switch v-if="group.deployments_enable" v-model="group.deployments_inbenta" label="INBENTA" color="#049372" style="margin-top:0px; margin-left:20px; margin-bottom:15px;" hide-details></v-switch>
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
            <v-card v-if="tabs==2" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">MONITORING</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch label="Access Monitoring" color="info" style="margin-top:0px;"></v-switch>
              </v-card-text>
            </v-card>

            <!-- UTILS -->
            <v-card v-if="tabs==3" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">UTILS</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch label="Access Utils" color="info" style="margin-top:0px;"></v-switch>
              </v-card-text>
            </v-card>

            <!-- JOBS -->
            <v-card v-if="tabs==4" style="margin-bottom:10px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">JOBS</v-toolbar-title>
              </v-toolbar>
              <v-card-text style="padding-bottom:0px;">
                <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px;">RIGHTS</div>
                <v-switch label="Access Jobs" color="info" style="margin-top:0px;"></v-switch>
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
      'deployments_execution_threads': 10,
      'deployments_execution_limit': null,
      'deployments_execution_concurrent': null
    },
    toolbar_title: '',
    form_valid: false,
    loading: false,

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
          this.group = response.data.group[0]
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    submitGroup() {
      this.loading = true
      if (this.group['id'] == null) this.newGroupSubmit()
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
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
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