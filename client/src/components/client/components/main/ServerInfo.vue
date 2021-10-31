<template>
  <div style="height:100%; overflow-y:auto;">
    <!----------------->
    <!-- SERVER INFO -->
    <!----------------->
    <v-container :style="`height:max(${height},100%); width:70%; display:flex; align-items:center; justify-content:center;`">
      <v-layout wrap>
        <v-flex v-show="item.length == 0" xs12>
          <div class="body-2" style="margin-top:1%; text-align:center;">Select a server to show the details</div>
        </v-flex>
        <v-flex ref="item" v-show="item.length != 0">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Server details</div>
          <v-card>
            <v-card-text style="padding:25px 20px 5px 20px; margin-bottom:20px;">
              <v-row no-gutters>
                <v-col cols="6" style="padding-right:10px">
                  <v-text-field v-model="item.name" readonly label="Name" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
                <v-col cols="6" style="padding-left:10px">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:8px">
                      <v-icon small :title="item.region_shared ? 'Shared' : 'Personal'" :color="item.region_shared ? '#EB5F5D' : 'warning'" style="margin-top:13px">{{ item.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                    </v-col>
                    <v-col>
                      <v-text-field v-model="item.region" readonly label="Region" r equired style="padding-top:0px; font-size:1rem;"></v-text-field>
                    </v-col>
                  </v-row>
                </v-col>
              </v-row>
              <!-- SQL -->
              <v-row no-gutters>
                <v-col cols="8" style="padding-right:10px">
                  <v-text-field v-model="item.engine" readonly label="Engine" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
                <v-col cols="4" style="padding-left:10px">
                  <v-text-field v-model="item.version" readonly label="Version" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
              </v-row>
              <div v-if="!(inventory_secured && !owner && item.shared)">
                <v-row no-gutters style="margin-top:10px;">
                  <v-col cols="8" style="padding-right:10px">
                    <v-text-field v-model="item.hostname" readonly label="Hostname" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                  </v-col>
                  <v-col cols="4" style="padding-left:10px">
                    <v-text-field v-model="item.port" readonly label="Port" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                  </v-col>
                </v-row>
                <v-text-field v-model="item.username" readonly label="Username" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                <v-text-field v-model="item.password" readonly label="Password" :append-icon="sqlPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="sqlPassword ? 'text' : 'password'" @click:append="sqlPassword = !sqlPassword" style="padding-top:0px; font-size:1rem;"></v-text-field>
              </div>
              <!-- SSL -->
              <v-card v-if="item.ssl" style="height:52px; margin-bottom:15px">
                <v-row no-gutters>
                  <v-col cols="auto" style="display:flex; margin:15px">
                    <v-icon color="#00b16a" style="font-size:20px">fas fa-key</v-icon>
                  </v-col>
                  <v-col>
                    <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a SSL connection</div>
                  </v-col>
                </v-row>
              </v-card>
              <!-- SSH -->
              <v-card v-if="item.ssh" style="height:52px; margin-bottom:15px">
                <v-row no-gutters>
                  <v-col cols="auto" style="display:flex; margin:15px">
                    <v-icon color="#2196f3" style="font-size:20px">fas fa-terminal</v-icon>
                  </v-col>
                  <v-col>
                    <div class="text-body-1" style="color:#2196f3; margin-top:15px">Using a SSH connection</div>
                  </v-col>
                </v-row>
              </v-card>
            </v-card-text>
          </v-card>
        </v-flex>
      </v-layout>
    </v-container>
  </div>
</template>

<script>
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      height: '100%',
      sqlPassword: false,
      sshPassword: false,
    }
  },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'sidebarSelected'
    ], { path: 'client/connection' }),
    item: function() {
      if (this.sidebarSelected.length == 0 || 'children' in this.sidebarSelected[this.sidebarSelected.length - 1]) return []
      else return this.sidebarSelected[this.sidebarSelected.length - 1]
    },
    owner: function() { return this.$store.getters['app/owner'] },
    inventory_secured: function() { return this.$store.getters['app/inventory_secured'] },
  },
  watch: {
    sidebarSelected (val) {
      if (val) {
        this.$nextTick(() => {
          if (this.$refs.item !== undefined && this.$refs.item.clientHeight != 0) {
            this.height = this.$refs.item.clientHeight + 25 + 'px'
          }
        })
      }
    },
  },
}
</script>